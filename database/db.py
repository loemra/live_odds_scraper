import dataclasses
import sqlite3
from threading import Lock
from typing import Callable, Tuple

from datastructures.event import Event
from datastructures.selection import Selection

_lock = Lock()
conn = sqlite3.connect("database/events.db")
cur = conn.cursor()


def _get_events() -> list[Event]:
    res = cur.execute("SELECT * FROM events")
    events = res.fetchall()
    return [Event(*event) for event in events]


def _get_unified_sport_name(sb: str, sport: str) -> str:
    res = cur.execute(
        "SELECT sport FROM sb_sports WHERE sb = ? AND name = ?", (sb, sport)
    )
    unified_sport = res.fetchone()
    if not unified_sport:
        raise Exception(
            f"_get_unified_sport_name unable to get sport name for {sb},"
            f" {sport}"
        )
    return unified_sport[0]


def _get_unified_market_name(sb: str, market: str) -> str:
    res = cur.execute(
        "SELECT market_id FROM sb_markets WHERE sb = ? AND name = ?",
        (sb, market),
    )
    unified_market = res.fetchone()
    if not unified_market:
        raise Exception(
            f"_get_unified_market_name unable to get sport name for {sb},"
            f" {market}"
        )
    return unified_market[0]


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
    modified_event = dataclasses.replace(event, id=str(cur.lastrowid))
    return modified_event


def _sb_event_exists(sb: str, id: str) -> bool:
    res = cur.execute(
        "SELECT COUNT(id) FROM sb_events WHERE sb = ? AND id = ?",
        (sb, id),
    )
    (exists,) = res.fetchone()
    return bool(exists)


def _register_sb_event(
    sb: str, sb_event_id: str, sb_event_url: str, event_id: str
):
    with conn:
        cur.execute(
            "INSERT INTO sb_events VALUES (?, ?, ?, ?)",
            (sb_event_id, sb_event_url, event_id, sb),
        )


def match_or_register_event(
    sb: str,
    event: Event,
    match_events: Callable[[Event, list[Event]], Event | None],
):
    with _lock:
        if _sb_event_exists(sb, event.id):
            return

        match = match_events(event, _get_events())
        if not match:
            event.sport = _get_unified_sport_name(sb, event.sport)
            match = _register_event(event)

        if not event.url:
            raise Exception(
                f"match_or_register_event sportsbook event has no url {event}"
            )
        _register_sb_event(sb, event.id, event.url, match.id)


def get_sb_events(sb: str) -> list[Tuple[str, str]]:
    res = cur.execute("SELECT event_id, url FROM sb_events WHERE sb = ?", (sb,))
    return res.fetchall()


def _update_odds(sb: str, id: str, odds: float):
    with conn:
        cur.execute(
            "UPDATE sb_selections SET odds = ? WHERE sb = ? AND id = ?",
            (str(odds), sb, id),
        )


def _sb_selection_exists(sb: str, id: str) -> bool:
    res = cur.execute(
        "SELECT COUNT(id) FROM sb_selections WHERE sb = ? AND id = ?", (sb, id)
    )
    (exists,) = res.fetchone()
    return bool(exists)


def _get_selections(
    unified_event_id: str, unified_market_id: str
) -> list[Selection]:
    res = cur.execute(
        (
            "SELECT id, name, link, market_id FROM selections WHERE event_id ="
            " ? AND market_id = ?"
        ),
        (unified_event_id, unified_market_id),
    )
    selections = res.fetchall()
    return [Selection(*selection) for selection in selections]


def _register_selection(
    sb: str, selection: Selection, event_id: str
) -> Selection:
    with conn:
        cur.execute(
            "INSERT INTO selections VALUES (NULL, ?, ?, ?, ?)",
            (selection.name, selection.link, event_id, selection.market_id),
        )
    modified_selection = dataclasses.replace(selection, id=str(cur.lastrowid))
    return modified_selection


def _register_sb_selection(
    sb: str, sb_selection_id: str, sb_odds: float | None, selection_id
):
    with conn:
        cur.execute(
            "INSERT INTO sb_selections VALUES (?, ?, ?, ?)",
            (
                sb_selection_id,
                (str(sb_odds) if sb_odds else "NULL"),
                selection_id,
                sb,
            ),
        )


def update_or_register_event_selections(
    sb: str,
    unified_event_id: str,
    selection: Selection,
    match_selection: Callable[[Selection, list[Selection]], Selection | None],
):
    with _lock:
        if _sb_selection_exists(sb, selection.id):
            if not selection.odds:
                raise Exception(
                    "update_or_register_event_selections trying to update"
                    f" selection with no odds {selection}"
                )
            _update_odds(sb, selection.id, selection.odds)
            return

        unified_market_id = _get_unified_market_name(sb, selection.market_id)

        match = match_selection(
            selection,
            _get_selections(unified_event_id, unified_market_id),
        )
        if not match:
            selection.market_id = unified_market_id
            match = _register_selection(sb, selection, unified_event_id)

        _register_sb_selection(sb, selection.id, selection.odds, match.id)
