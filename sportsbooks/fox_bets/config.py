import json
from datetime import datetime

from datastructures.market import MarketKind


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


def get_market_kind(market_id: str) -> MarketKind:
    for s in _config["sports"].values():
        kind = s["markets"].get(market_id)
        if kind:
            return MarketKind[kind]
    raise Exception(f"Unable to find kind for id {market_id} fox_bets")
