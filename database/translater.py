import json
from threading import Lock


EVENT_ID_TRANSLATER = "database/event_id_translater.json"
SPORT_TRANSLATER = "database/sport_translater.json"


# must hold lock when calling anything.
lock = Lock()


def _get_translater(filename: str):
    with open(filename, "r") as f:
        return json.load(f)


def _write_translater(filename: str, j):
    with open(filename, "w") as f:
        json.dump(j, f)


def create_event(unified_id: str, translate: dict[str, str]):
    j = _get_translater(EVENT_ID_TRANSLATER)
    j["events"][unified_id] = translate
    _write_translater(EVENT_ID_TRANSLATER, j)


def get_event_id_translater(sportsbook: str):
    j = _get_translater(EVENT_ID_TRANSLATER)

    translater = {}

    for unified_id, sportsbook_ids in j["events"].items():
        if sportsbook in sportsbook_ids:
            translater[sportsbook_ids[sportsbook]] = unified_id

    return translater


def get_sport_translater(sportsbook: str):
    j = _get_translater(SPORT_TRANSLATER)

    translater = {}

    for unified_sport, sportsbook_sports in j["sports"].items():
        if sportsbook in sportsbook_sports:
            translater[sportsbook_sports[sportsbook]] = unified_sport

    return translater
