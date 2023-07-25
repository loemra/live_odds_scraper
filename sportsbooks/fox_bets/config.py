import json
from datetime import datetime
from typing import Optional

from datastructures.market import Kind, Name, Period


def _get_config():
    with open("sportsbooks/fox_bets/config.json", "r") as f:
        return json.load(f)


_config = _get_config()


def get_events_urls(date: datetime) -> list[str]:
    event_urls = []
    for sport in _config["sports"]:
        event_urls.append(
            _config["get_events_url"].format(sport, date.strftime(r"%Y-%m-%d"))
        )
    return event_urls


def get_event_url(id: str) -> str:
    return _config["get_event_url"].format(id)


def is_market(market: str) -> bool:
    for s in _config["sports"].values():
        if market in s["markets"].keys():
            return True
    return False


def get_headers() -> dict[str, str]:
    return _config["headers"]


def get_name(sport: str, id: str) -> Name:
    return Name[_config["sports"][sport]["markets"][id]["name"]]


def get_kind(sport: str, id: str) -> Kind:
    return Kind[_config["sports"][sport]["markets"][id]["kind"]]


def get_period(sport: str, period: Optional[str]) -> Period:
    if not period:
        return Period.REGULAR
    return Period[_config["sports"][sport]["periods"][period]]
