from datastructures.event import EventMetadata
from datastructures.market import MarketMetadata
from datastructures.selection import Selection
from threading import Lock
from datetime import datetime
import json
from collections.abc import Callable


# TODO: Figure out a better database solution, not json files.

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


def _get_events() -> list[EventMetadata]:
    database = _get_database()
    events = []
    for unified_id, event in database["events"].items():
        datetime_str = event["date"]
        date = datetime.fromtimestamp(datetime_str)
        events.append(EventMetadata(unified_id, event["name"], event["sport"], date))
    return events


def _register_event(event: EventMetadata):
    database = _get_database()
    event_dict = event.to_json()
    event_dict.pop("id")
    database["events"][event.id] = event_dict
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
        _register_event(event)
        return event


def _get_markets(event_id: str) -> list[MarketMetadata]:
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_get_markets() {event_id} not found in database.")

    event = database["events"][event_id]
    markets = []

    if "markets" not in event:
        return markets

    for market_id, market in event["markets"].items():
        markets.append(MarketMetadata(market_id))

    return markets


def _register_market(event_id: str, market: MarketMetadata):
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_register_market() {event_id} not found in database.")

    event = database["events"][event_id]
    if "markets" not in event:
        event["markets"] = {}

    event["markets"][market.code] = {}

    _write_database(database)


def match_or_register_market(
    event_id: str,
    maybe_match: Callable[[list[MarketMetadata]], MarketMetadata | None],
    unify: Callable[[], MarketMetadata],
) -> MarketMetadata:
    with _lock:
        markets = _get_markets(event_id)

        market = maybe_match(markets)
        if market:
            return market

        market = unify()
        _register_market(event_id, market)
        return market


def _get_selection(event_id: str, market_id: str) -> list[Selection]:
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_get_selection() {event_id} not found in database.")
    event = database["events"][event_id]
    if market_id not in event["markets"]:
        raise Exception(f"_get_selection() {market_id} not found in event {event}.")
    market = event["markets"][market_id]

    selection = []
    if "selection" not in market:
        return selection

    for selection_id, s in market["selection"].items():
        selection.append(Selection(selection_id, s["name"], s["odds"]))

    return selection


def _register_selection(event_id: str, market_id: str, selection: Selection):
    database = _get_database()
    if event_id not in database["events"]:
        raise Exception(f"_register_selection() {event_id} not found in database.")
    event = database["events"][event_id]
    if market_id not in event["markets"]:
        raise Exception(
            f"_register_selection() {market_id} not found in event {event}."
        )
    market = event["markets"][market_id]

    if "selection" not in market:
        market["selection"] = {}

    market["selection"][selection.id] = {"name": selection.name, "odds": selection.odds}
    _write_database(database)


def match_or_register_selection(
    event_id: str,
    market_id: str,
    maybe_match: Callable[[list[Selection]], Selection | None],
    unify: Callable[[], Selection],
):
    with _lock:
        selection = _get_selection(event_id, market_id)

        selection = maybe_match(selection)
        if selection:
            return selection

        selection = unify()
        _register_selection(event_id, market_id, selection)
        return selection
