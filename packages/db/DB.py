import dataclasses
import sqlite3
from datetime import timedelta
from threading import Lock
from typing import List

from packages.data.EventRegistration import EventRegistration
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.MockSB import Event


class DB:
    def __init__(self, name):
        self.con = sqlite3.connect(name)
        self.lock = Lock()

    def match_or_make_event(
        self, sb_event, sb, name_matcher: NameMatcher
    ) -> EventRegistration:
        with self.lock:
            relevant_events = self._get_relevant_events(sb_event)
            unified_event_index = name_matcher.match(
                sb_event.name, [e.name for e in relevant_events]
            )

            # no match.
            if unified_event_index is None:
                unified_event = self._make_unified_event(sb_event)
            else:
                unified_event = relevant_events[unified_event_index]

            self._make_sb_event(sb_event, sb, unified_event)

            er = EventRegistration(sb_event.id, unified_event.id)

            self._match_or_make_markets(
                unified_event.id, sb_event.markets, sb, name_matcher, er
            )

        return er

    def _get_relevant_events(
        self, event: Event, relevant_date_delta=timedelta(minutes=30)
    ) -> List[Event]:
        lower_bound_date = (event.date - relevant_date_delta).timestamp()
        upper_bound_date = (event.date + relevant_date_delta).timestamp()
        sport = str(event.sport)

        cur = self.con.cursor()
        res = cur.execute(
            """
        SELECT * FROM events e 
        WHERE e.date >= ? AND e.date <= ? AND sport = ?
                    """,
            (lower_bound_date, upper_bound_date, sport),
        )

        relevant_events = []
        for i in res:
            relevant_events.append(Event.fromdb(*i))

        return relevant_events

    def _make_unified_event(self, sb_event) -> Event:
        with self.con:
            cur = self.con.cursor()

            cur.execute(
                """
                INSERT INTO events VALUES
                    (NULL, ?, ?, ?)
            """,
                (
                    sb_event.name,
                    sb_event.date.timestamp(),
                    sb_event.sport,
                ),
            )
            unified_event_id = cur.lastrowid

        if unified_event_id is None:
            raise Exception("Unable to make unified event.")
        unified_event = dataclasses.replace(sb_event, id=unified_event_id)

        return unified_event

    def _make_sb_event(self, unified_event_id, sb, sb_event: Event):
        with self.con:
            cur = self.con.cursor()
            cur.execute(
                """
                INSERT INTO sb_events VALUES
                    (?, ?, ?, ?)
            """,
                (sb_event.id, sb, sb_event.name, unified_event_id),
            )

    def _match_or_make_markets(
        self,
        unified_event_id,
        sb_markets,
        sb,
        name_matcher: NameMatcher,
        er: EventRegistration,
    ):
        for sb_market in sb_markets:
            relevant_markets = self._get_relevant_markets(
                unified_event_id, sb_market
            )
            matched_market_index = name_matcher.match(
                sb_market.participant, [m.participant for m in relevant_markets]
            )

            # no match.
            if matched_market_index is None:
                market = self._make_market(unified_event_id, sb_market)
            else:
                market = relevant_markets[matched_market_index]

            self._match_or_make_selections(
                market.id, sb_market.selection, sb, name_matcher, er
            )

    def _get_relevant_markets(
        self, unified_event_id, market: Market
    ) -> List[Market]:
        cur = self.con.cursor()
        res = cur.execute(
            """
            SELECT id, name, kind, period, participant, line
            FROM markets
            WHERE name = ? AND kind = ? AND period = ?
            AND line = ? AND event_id = ?
        """,
            (
                market.name,
                market.kind,
                market.period,
                market.line,
                unified_event_id,
            ),
        )

        relevant_markets = []
        for i in res:
            potential_market = Market.fromdb(*i)
            if (market.participant is None) == (
                potential_market.participant is None
            ):
                relevant_markets.append(Market.fromdb(*i))

        return relevant_markets

    def _make_market(self, unified_event_id, market: Market) -> Market:
        with self.con:
            cur = self.con.cursor()
            cur.execute(
                """
                INSERT INTO markets VALUES
                    (NULL, ?, ?, ?, ?, ?, ?)
                """,
                (
                    market.name,
                    market.kind,
                    market.period,
                    market.participant,
                    market.line,
                    unified_event_id,
                ),
            )

        if cur.lastrowid is None:
            raise Exception(
                f"Unable to make market. {unified_event_id}\n{market}"
            )

        return dataclasses.replace(market, id=cur.lastrowid)

    def _match_or_make_selections(
        self,
        market_id,
        sb_selections: List[Selection],
        sb,
        name_matcher: NameMatcher,
        er: EventRegistration,
    ):
        for sb_selection in sb_selections:
            relevant_selections = self._get_relevant_selections(market_id)
            matched_selection_index = name_matcher.match(
                sb_selection.name, [s.name for s in relevant_selections]
            )

            # no match.
            if matched_selection_index is None:
                selection = self._make_selection(market_id, sb_selection)
            else:
                selection = relevant_selections[matched_selection_index]

            self._make_sb_selection(selection.id, sb_selection, sb)

            er.sb_to_unified_selection[sb_selection.id] = selection.id
            er.unified_to_sb_selection[selection.id] = sb_selection.id

    def _get_relevant_selections(self, market_id) -> List[Selection]:
        cur = self.con.cursor()
        res = cur.execute(
            """
            SELECT id, name
            FROM selections
            WHERE market_id = ?
        """,
            (market_id),
        )

        relevant_selections = []
        for i in res:
            relevant_selections.append(*i)

        return relevant_selections

    def _make_selection(self, market_id, sb_selection):
        with self.con:
            cur = self.con.cursor()
            cur.execute(
                """
                INSERT INTO selections VALUES
                    (NULL, ?, ?)
            """,
                (sb_selection.name, market_id),
            )

        if cur.lastrowid is None:
            raise Exception(
                f"Unable to make selection. {market_id}\n{sb_selection}"
            )

        return dataclasses.replace(sb_selection, id=cur.lastrowid)

    def _make_sb_selection(self, selection_id, sb_selection, sb):
        with self.con:
            cur = self.con.cursor()
            cur.execute(
                """
                INSERT INTO sb_selections VALUES
                    (?, ?, NULL, ?)
            """,
                (sb_selection.id, sb, selection_id),
            )

        if cur.lastrowid is None:
            raise Exception(
                f"Unable to make sb_selection. {selection_id}\n{sb_selection}"
            )
