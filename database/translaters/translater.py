import json
import logging
from threading import Lock


def _setup_logger():
    logger = logging.getLogger("events_database")
    logger.propagate = False
    fh = logging.FileHandler("logs/events_database.log")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s @ %(filename)s:%(funcName)s:%(lineno)s =="
        " %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


_logger = _setup_logger()


# Dynamic
EVENT_ID_TRANSLATER = "database/translaters/event_id_translater.json"
EVENT_NAME_TRANSLATER = "database/translaters/event_name_translater.json"
SELECTION_ID_TRANSLATER = "database/translaters/selection_id_translater.json"
SELECTION_NAME_TRANSLATER = (
    "database/translaters/selection_name_translater.json"
)

# Static
SPORT_TRANSLATER = "database/translaters/sport_translater.json"
MARKET_ID_TRANSLATER = "database/translaters/market_id_translater.json"


# public functions can not hold lock before calling.
# private function need to hold lock before calling.
_lock = Lock()


def _get_translater(filename: str):
    with open(filename, "r") as f:
        return json.load(f)


def _write_translater(filename: str, j):
    with open(filename, "w") as f:
        json.dump(j, f)


def _maybe_register(
    translater: str, sportsbook: str, sportsbook_id: str, unified_id: str
):
    j = _get_translater(translater)
    if unified_id not in j:
        j[unified_id] = {}
    j[unified_id][sportsbook] = sportsbook_id
    _write_translater(translater, j)


def _sportsbook_to_unified(
    translater: str, sportsbook: str, sportsbook_id: str
) -> str | None:
    j = _get_translater(translater)

    for unified_id, sportsbook_ids in j.items():
        if sportsbook_ids.get(sportsbook) == sportsbook_id:
            return unified_id

    return None


def _unified_to_sportsbook(
    translater: str, sportsbook: str, unified_id: str
) -> str | None:
    j = _get_translater(translater)

    if unified_id in j:
        if sportsbook in j[unified_id]:
            return j[unified_id][sportsbook]

    return None


def reset_translaters():
    with _lock:
        _write_translater(EVENT_ID_TRANSLATER, {})
        _write_translater(EVENT_NAME_TRANSLATER, {})
        _write_translater(SELECTION_ID_TRANSLATER, {})
        _write_translater(SELECTION_NAME_TRANSLATER, {})


# EVENT


def maybe_register_event_id(
    sportsbook: str, sportsbook_id: str, unified_id: str
):
    with _lock:
        _maybe_register(
            EVENT_ID_TRANSLATER, sportsbook, sportsbook_id, unified_id
        )


def sportsbook_to_unified_event_id(
    sportsbook: str, sportsbook_id: str
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            EVENT_ID_TRANSLATER, sportsbook, sportsbook_id
        )


def unified_to_sportsbook_event_id(
    sportsbook: str, unified_id: str
) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            EVENT_ID_TRANSLATER, sportsbook, unified_id
        )


def maybe_register_event_name(
    sportsbook: str, sportsbook_name: str, unified_name: str
):
    with _lock:
        _maybe_register(
            EVENT_NAME_TRANSLATER, sportsbook, sportsbook_name, unified_name
        )


def sportsbook_to_unified_event_name(
    sportsbook: str, sportsbook_name: str
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            EVENT_NAME_TRANSLATER, sportsbook, sportsbook_name
        )


def unified_to_sportsbook_event_name(
    sportsbook: str, unified_name: str
) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            EVENT_NAME_TRANSLATER, sportsbook, unified_name
        )


# MARKET


def sportsbook_to_unified_sport(
    sportsbook: str, sportsbook_sport: str
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            SPORT_TRANSLATER, sportsbook, sportsbook_sport
        )


def unified_to_sportsbook_sport(
    sportsbook: str, unified_sport: str
) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            SPORT_TRANSLATER, sportsbook, unified_sport
        )


def sportsbook_to_unified_market_id(
    sportsbook: str, sportsbook_id: str
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            MARKET_ID_TRANSLATER, sportsbook, sportsbook_id
        )


def unified_to_sportsbook_market_id(sportsbook: str, unified_id) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            MARKET_ID_TRANSLATER, sportsbook, unified_id
        )


# SELECTION


def maybe_register_selection_id(
    sportsbook: str, sportsbook_id: str, unified_id: str
):
    with _lock:
        _maybe_register(
            SELECTION_ID_TRANSLATER, sportsbook, sportsbook_id, unified_id
        )


def sportsbook_to_unified_selection_id(
    sportsbook: str, sportsbook_id: str
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            SELECTION_ID_TRANSLATER, sportsbook, sportsbook_id
        )


def unified_to_sportsbook_selection_id(
    sportsbook: str, unified_id: str
) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            SELECTION_ID_TRANSLATER, sportsbook, unified_id
        )


def maybe_register_selection_name(
    sportsbook: str, sportsbook_name: str, unified_name: str
):
    with _lock:
        _maybe_register(
            SELECTION_NAME_TRANSLATER, sportsbook, sportsbook_name, unified_name
        )


def sportsbook_to_unified_selection_name(
    sportsbook: str, sportsbook_name
) -> str | None:
    with _lock:
        return _sportsbook_to_unified(
            SELECTION_NAME_TRANSLATER, sportsbook, sportsbook_name
        )


def unified_to_sportsbook_selection_name(
    sportsbook: str, unified_name
) -> str | None:
    with _lock:
        return _unified_to_sportsbook(
            SELECTION_NAME_TRANSLATER, sportsbook, unified_name
        )
