import json
from threading import Lock


EVENT_ID_TRANSLATER = "database/translaters/event_id_translater.json"
SELECTION_ID_TRANSLATER = "database/translaters/selection_id_translater.json"
SPORT_TRANSLATER = "database/translaters/sport_translater.json"
MARKET_TRANSLATER = "database/translaters/market_translater.json"


# public functions can not hold lock before calling.
# private function need to hold lock before calling.
_lock = Lock()


def _get_translater(filename: str):
    with open(filename, "r") as f:
        return json.load(f)


def _write_translater(filename: str, j):
    with open(filename, "w") as f:
        json.dump(j, f)


def maybe_register_event(sportsbook: str, sportsbook_id: str, unified_id: str):
    with _lock:
        j = _get_translater(EVENT_ID_TRANSLATER)
        if unified_id not in j["events"]:
            j["events"][unified_id] = {}
        j["events"][unified_id][sportsbook] = sportsbook_id
        _write_translater(EVENT_ID_TRANSLATER, j)


def get_event_id_translater(sportsbook: str):
    with _lock:
        j = _get_translater(EVENT_ID_TRANSLATER)

        translater = {}

        for unified_id, sportsbook_ids in j["events"].items():
            if sportsbook in sportsbook_ids:
                translater[sportsbook_ids[sportsbook]] = unified_id

        return translater


def maybe_register_selection(sportsbook: str, sportsbook_id: str, unified_id: str):
    with _lock:
        j = _get_translater(SELECTION_ID_TRANSLATER)
        if unified_id not in j["selection"]:
            j["selection"][unified_id] = {}
        j["selection"][unified_id][sportsbook] = sportsbook_id
        _write_translater(SELECTION_ID_TRANSLATER, j)


def get_selection_id_translater(sportsbook: str):
    with _lock:
        j = _get_translater(SELECTION_ID_TRANSLATER)

        translater = {}

        for unified_id, sportsbook_ids in j["selection"].items():
            if sportsbook in sportsbook_ids:
                translater[sportsbook_ids[sportsbook]] = unified_id

        return translater


def get_sport_translater(sportsbook: str):
    with _lock:
        j = _get_translater(SPORT_TRANSLATER)

        translater = {}

        for unified_sport, sportsbook_sports in j["sports"].items():
            if sportsbook in sportsbook_sports:
                translater[sportsbook_sports[sportsbook]] = unified_sport

        return translater


def get_market_translater(sportsbook: str):
    with _lock:
        j = _get_translater(MARKET_TRANSLATER)

        translater = {}

        for unified_market, sportsbook_market in j["markets"].items():
            if sportsbook in sportsbook_market:
                translater[sportsbook_market[sportsbook]] = unified_market

        return translater
