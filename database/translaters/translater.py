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


def translate_event_id(sportsbook: str, event_id: str) -> str | None:
    with _lock:
        j = _get_translater(EVENT_ID_TRANSLATER)

        for unified_id, sportsbook_ids in j["events"].items():
            if sportsbook_ids.get(sportsbook) == event_id:
                return unified_id

        return None


def translate_event_id_to_sportsbook(
    sportsbook: str, unified_event_id: str
) -> str | None:
    with _lock:
        j = _get_translater(EVENT_ID_TRANSLATER)

        if unified_event_id in j["events"]:
            if sportsbook in j["events"][unified_event_id]:
                return j["events"][unified_event_id][sportsbook]

        return None


def maybe_register_selection(sportsbook: str, sportsbook_id: str, unified_id: str):
    with _lock:
        j = _get_translater(SELECTION_ID_TRANSLATER)
        if unified_id not in j["selection"]:
            j["selection"][unified_id] = {}
        j["selection"][unified_id][sportsbook] = sportsbook_id
        _write_translater(SELECTION_ID_TRANSLATER, j)


def translate_selection_id(sportsbook: str, selection_id: str) -> str | None:
    with _lock:
        j = _get_translater(SELECTION_ID_TRANSLATER)

        for unified_id, sportsbook_ids in j["selection"].items():
            if sportsbook_ids.get(sportsbook) == selection_id:
                return unified_id

        return None


def translate_sport(sportsbook: str, sport: str) -> str | None:
    with _lock:
        j = _get_translater(SPORT_TRANSLATER)

        for unified_sport, sportsbook_sports in j["sports"].items():
            if sportsbook_sports.get(sportsbook) == sport:
                return unified_sport

        return None


def translate_market(sportsbook: str, market_id) -> str | None:
    with _lock:
        j = _get_translater(MARKET_TRANSLATER)

        for unified_market, sportsbook_market in j["markets"].items():
            if sportsbook_market.get(sportsbook) == market_id:
                return unified_market

        return None


def translate_market_to_sportsbook(sportsbook: str, unified_market_id) -> str | None:
    with _lock:
        j = _get_translater(MARKET_TRANSLATER)

        if unified_market_id in j["markets"]:
            if sportsbook in j["markets"][unified_market_id]:
                return j["markets"][unified_market_id][sportsbook]

        return None
