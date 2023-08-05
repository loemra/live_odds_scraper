import json
import logging
from datetime import datetime

import pytz

from datastructures.event import Sport
from datastructures.market import Kind, Name, Period

log = logging.getLogger(__name__)


def _get_config():
    with open("sportsbooks/fanduel/config.json", "r") as f:
        return json.load(f)


_config = _get_config()


def get_events_urls() -> list[str]:
    event_urls = []
    for sport in _config["sports"]:
        event_urls.append(_config["get_events_url"].format(sport))
    return event_urls


def get_event_url(event_id: str) -> str:
    return _config["get_event_url"].format(event_id)


def get_sport(sport: str) -> Sport:
    return Sport[_config["sports"][sport]["name"]]


def get_date(date: str) -> datetime:
    return datetime.fromisoformat(date[:-1]).astimezone(
        pytz.timezone("US/EASTERN")
    )


def is_market(market: str) -> bool:
    for s in _config["sports"].values():
        if market in s["markets"].keys():
            return True
    return False


def get_name(sport: str, id: str) -> Name:
    return Name[_config["sports"][sport]["markets"][id]["name"]]


def get_kind(sport: str, id: str) -> Kind:
    return Kind[_config["sports"][sport]["markets"][id]["kind"]]


def get_period(sport: str, period: str) -> Period:
    return Period[_config["sports"][sport]["periods"][period]]
