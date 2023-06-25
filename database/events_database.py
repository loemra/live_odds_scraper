from threading import Lock
from datastructures.event_metadata import EventMetadata
from datetime import datetime
import json


DATABASE_NAME = "database/events.json"

# must hold lock when calling anything.
lock = Lock()


def _get_database():
    with open(DATABASE_NAME, "r") as f:
        return json.load(f)


def _write_database(j):
    with open(DATABASE_NAME, "w") as f:
        json.dump(j, f)


def register_new_event(event: EventMetadata):
    database = _get_database()
    event_dict = event.to_json()
    event_dict.pop("id")
    database["events"][event.id] = event_dict
    _write_database(database)


def get_events() -> list[EventMetadata]:
    database = _get_database()
    events = []
    for unified_id, event in database["events"].items():
        datetime_str = event["date"]
        date = datetime.fromtimestamp(datetime_str)
        events.append(EventMetadata(unified_id, event["name"], event["sport"], date))
    return events


def get_event_metadata(unified_id: str) -> EventMetadata:
    pass
