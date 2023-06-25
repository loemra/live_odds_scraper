from datastructures.event import EventMetadata
from datastructures.market import MarketMetadata
from threading import Lock
from datetime import datetime
import json
from collections.abc import Callable


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
        raise f"_get_markets() {event_id} not found in database."

    event = database["events"][event_id]
    markets = []

    if "markets" not in event:
        return markets

    for market_id, _ in event["markets"].items():
        markets.append(MarketMetadata(market_id))

    return markets


def _register_market(event_id: str, market: MarketMetadata):
    database = _get_database()
    if event_id not in database["events"]:
        raise f"_register_market() {event_id} not found in database."

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
