import json
from collections.abc import Callable
from datetime import datetime
from threading import Lock

from datastructures.event import Event, EventMetadata
from datastructures.market import MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from datastructures.update import Update

"""
GENERAL STRUCTURE
- get_*s
    Will return a list of * metadata.
- get_
    Will return a single fully populated *.
- match_or_register_*
    For determining whether a * already exists in the
    database, if not add it.
- update_odds
    The only thing that can be updated in the database
    are odds for a sportsbook, the rest is const.
"""


DATABASE_NAME = "database/events.json"

# public functions can not hold lock before calling.
# private function need to hold lock before calling.
_lock = Lock()


def _get_database():
    with open(DATABASE_NAME, "r") as f:
        return json.load(f)


def _write_database(j):
    with open(DATABASE_NAME, "w") as f:
        json.dump(j, f)


# EVENT


def _get_events() -> list[EventMetadata]:
    database = _get_database()
    events = []
    for unified_id, event in database["events"].items():
        datetime_str = event["date"]
        date = datetime.fromtimestamp(datetime_str)
        events.append(EventMetadata(unified_id, event["name"], event["sport"], date))
    return events


def get_events() -> list[EventMetadata]:
    with _lock:
        return _get_events()


def get_event(event_id: str) -> Event:
    pass


def _maybe_register_event(event: EventMetadata):
    database = _get_database()

    if event.id in database["events"]:
        return

    database["events"][event.id] = {
        "name": event.name,
        "sport": event.sport,
        "date": event.date.timestamp(),
    }
    _write_database(database)


def match_or_register_event(
    maybe_match: Callable[[list[EventMetadata]], EventMetadata | None],
    unify: Callable[[], EventMetadata],
) -> EventMetadata:
    with _lock:
        events = _get_events()

        event = maybe_match(events)
        if event:
            return event

        event = unify()
        _maybe_register_event(event)
        return event


# MARKET


def _get_markets(event_id: str) -> list[MarketMetadata]:
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_get_markets() {event_id} not found in database.")

    event = database["events"][event_id]
    markets = []

    if "markets" not in event:
        return markets

    for market_id in event["markets"]:
        markets.append(MarketMetadata(market_id))

    return markets


def get_markets(event_id: str) -> list[MarketMetadata]:
    with _lock:
        return _get_markets(event_id)


# TODO: def get_market(event_id: str, market_id: str) -> Market:


def _maybe_register_market(event_id: str, market: MarketMetadata):
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_register_market() {event_id} not found in database.")

    event = database["events"][event_id]
    if "markets" not in event:
        event["markets"] = {}

    if market.id in event["markets"]:
        return

    event["markets"][market.id] = {}

    _write_database(database)


def maybe_register_market(event_id: str, market: MarketMetadata):
    with _lock:
        _maybe_register_market(event_id, market)


# SELECTION


def _get_selections(event_id: str, market_id: str) -> list[SelectionMetadata]:
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_get_selection() {event_id} not found in database.")
    event = database["events"][event_id]
    if market_id not in event["markets"]:
        raise Exception(f"_get_selection() {market_id} not found in event {event}.")
    market = event["markets"][market_id]

    selections = []
    if "selection" not in market:
        return selections

    for selection_id, s in market["selection"].items():
        selections.append(SelectionMetadata(selection_id, s["name"]))

    return selections


# TODO: def get_selections(event_id: str, market_id: str) -> list[SelectionMetadata]:
# TODO: def get_selection(event_id: str, market_id: str, selection_id: str) -> Selection:


def _maybe_register_selection(event_id: str, market_id: str, selection: SelectionMetadata):
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_register_selection() {event_id} not found in database.")
    event = database["events"][event_id]
    if market_id not in event["markets"]:
        raise Exception(f"_register_selection() {market_id} not found in event {event}.")
    market = event["markets"][market_id]

    if "selection" not in market:
        market["selection"] = {}

    if selection.id in market["selection"]:
        return

    market["selection"][selection.id] = {"name": selection.name}
    _write_database(database)


def match_or_register_selection(
    event_id: str,
    market_id: str,
    maybe_match: Callable[[list[SelectionMetadata]], SelectionMetadata | None],
    unify: Callable[[], SelectionMetadata],
) -> SelectionMetadata:
    with _lock:
        selection = _get_selections(event_id, market_id)

        selection = maybe_match(selection)
        if selection:
            return selection

        selection = unify()
        _maybe_register_selection(event_id, market_id, selection)
        return selection


# UPDATE


def update_event_odds(update: Update):
    with _lock:
        database = _get_database()
        if update.event_id not in database["events"]:
            raise Exception(f"update_event_odds() {update.event_id} not found in database.")
        event = database["events"][update.event_id]
        if update.market_id not in event["markets"]:
            raise Exception(f"update_event_odds() {update.market_id} not found in event {event}.")
        market = event["markets"][update.market_id]
        if update.selection_id not in market["selection"]:
            raise Exception(f"update_event_odds() {update.selection_id} not found in market" f" {market}.")

        market["selection"][update.selection_id]["odds"] = update.new_odds
        print("updating" f" {update.event_id}/{update.market_id}/{update.selection_id} with" f" {update.new_odds}")
        _write_database(database)
