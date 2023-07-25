import dataclasses
import sqlite3
from datetime import datetime
from typing import Callable, Optional, Tuple

from datastructures.event import Event
from datastructures.market import Market
from datastructures.selection import Selection

conn = sqlite3.connect("database/events.db")
cur = conn.cursor()


def _get_events() -> list[Event]:
    res = cur.execute("SELECT * FROM events")
    events = res.fetchall()
    return [Event(*event) for event in events]


def _register_event(event: Event) -> Event:
    with conn:
        cur.execute(
            "INSERT INTO events VALUES (NULL, ?, ?, ?)",
            (
                event.name,
                event.sport,
                event.date.timestamp(),
            ),
        )
    if not cur.lastrowid:
        raise Exception(f"_register_event, unable to get row_id for {event}")
    modified_event = dataclasses.replace(event, id=cur.lastrowid)
    return modified_event


def _sb_event_exists(sb: str, id: str) -> bool:
    res = cur.execute(
        "SELECT COUNT(id) FROM sb_events WHERE sb = ? AND id = ?",
        (sb, id),
    )
    (exists,) = res.fetchone()
    return bool(exists)


def _register_sb_event(
    sb: str, sb_event_id: str, sb_event_url: str, event_id: int, sb_name: str
):
    with conn:
        cur.execute(
            "INSERT INTO sb_events VALUES (?, ?, ?, ?, ?)",
            (sb_event_id, sb, sb_name, sb_event_url, event_id),
        )


def match_or_register_event(
    lock,
    sb: str,
    event: Event,
    match_events: Callable[[Event, list[Event]], Event | None],
):
    with lock:
        if _sb_event_exists(sb, event.id):
            return

        match = match_events(event, _get_events())
        if not match:
            match = _register_event(event)

        if not event.url:
            raise Exception(
                f"match_or_register_event sportsbook event has no url {event}"
            )
        _register_sb_event(sb, event.id, event.url, int(match.id), event.name)


def get_sb_events(lock, sb: str) -> list[Tuple[int, str]]:
    # return events that have not started.
    now = datetime.now().timestamp()
    with lock:
        res = cur.execute(
            "SELECT sb_events.event_id, sb_events.url FROM sb_events, events"
            " WHERE sb_events.sb = ? AND events.id = sb_events.event_id AND"
            " events.date > ?",
            (sb, now),
        )
        return res.fetchall()


def _sb_market_exists(sb: str, market_id: str) -> Optional[int]:
    res = cur.execute(
        "SELECT market_id FROM sb_markets WHERE sb = ? AND id = ?",
        (sb, market_id),
    )
    (unified_market_id,) = res.fetchone()
    return unified_market_id


def _get_markets(unified_event_id: int) -> list[Market]:
    res = cur.execute(
        "SELECT rowid, name, kind, period, player, line FROM markets WHERE"
        " event_id = ?",
        (unified_event_id,),
    )
    return [Market(*m) for m in res.fetchall()]


def _register_market(unified_event_id: int, market: Market) -> Market:
    with conn:
        cur.execute(
            "INSERT INTO markets VALUES (NULL, ?, ?, ?, ?, ?, ?)",
            (
                market.name,
                market.kind,
                market.period,
                market.player,
                market.line,
                unified_event_id,
            ),
        )
    if not cur.lastrowid:
        raise Exception(f"_register_market, unable to get row_id for {market}")
    return dataclasses.replace(market, id=cur.lastrowid)


def _register_sb_market(sb: str, market: Market, unified_market_id: int):
    with conn:
        cur.execute(
            "INSERT INTO markets VALUES (?, ?, ?, ?)",
            (
                market.id,
                sb,
                market.player,
                unified_market_id,
            ),
        )


def match_or_register_market(
    lock,
    sb: str,
    unified_event_id: int,
    market: Market,
    maybe_match_market: Callable[[Market, list[Market]], Market | None],
) -> int:
    with lock:
        unified_market_id = _sb_market_exists(sb, market.id)
        if unified_market_id is not None:
            return unified_market_id

        match = maybe_match_market(market, _get_markets(unified_event_id))
        if not match:
            match = _register_market(unified_event_id, market)

        _register_sb_market(sb, market, int(match.id))

        return int(match.id)


def _update_odds(sb: str, id: str, odds: float):
    with conn:
        cur.execute(
            "UPDATE sb_selections SET odds = ? WHERE sb = ? AND id = ?",
            (odds, sb, id),
        )
        cur.execute(
            "INSERT INTO history VALUES (?, ?, ?)",
            (odds, int(datetime.now().timestamp()), id),
        )


def _sb_selection_exists(sb: str, id: str) -> Optional[int]:
    res = cur.execute(
        "SELECT selection_id FROM sb_selections WHERE sb = ? AND id = ?",
        (sb, id),
    )
    (selection_id,) = res.fetchone()
    return selection_id


def _get_selections(unified_market_id: int) -> list[Selection]:
    res = cur.execute(
        "SELECT rowid, name, FROM selections WHERE market_id = ?",
        (unified_market_id,),
    )
    selections = res.fetchall()
    return [Selection(*selection) for selection in selections]


def _register_selection(selection: Selection, unified_market_id: int) -> int:
    with conn:
        cur.execute(
            "INSERT INTO selections VALUES (NULL, ?, ?)",
            (selection.name, unified_market_id),
        )
    unified_selection_id = cur.lastrowid
    if not unified_selection_id:
        raise Exception(
            f"Couldn't register selection {selection}, {unified_market_id}"
        )
    return unified_selection_id


def _register_sb_selection(
    sb: str,
    sb_selection_id: str,
    sb_odds: float | None,
    selection_id: int,
):
    with conn:
        cur.execute(
            "INSERT INTO sb_selections VALUES (?, ?, ?, ?, ?)",
            (
                sb_selection_id,
                sb,
                sb_odds,
                selection_id,
            ),
        )
        cur.execute(
            "INSERT INTO history VALUES (?, ?, ?)",
            (sb_odds, int(datetime.now().timestamp()), sb_selection_id),
        )


def update_or_register_event_selection(
    lock,
    sb: str,
    unified_market_id: int,
    selection: Selection,
    match_selection: Callable[[Selection, list[Selection]], Selection | None],
):
    with lock:
        if _sb_selection_exists(sb, selection.id):
            if not selection.odds:
                raise Exception(
                    "update_or_register_event_selections trying to update"
                    f" selection with no odds {selection}"
                )
            _update_odds(sb, selection.id, selection.odds)
            return

        match = match_selection(
            selection,
            _get_selections(unified_market_id),
        )
        if not match:
            unified_selection_id = _register_selection(
                selection, unified_market_id
            )
        else:
            unified_selection_id = int(match.id)

        _register_sb_selection(
            sb, selection.id, selection.odds, unified_selection_id
        )
