import json
import urllib.parse
from datetime import datetime
from typing import Tuple

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


def get_event_url(id: str, sport: str) -> str:
    markets = ",".join(
        [
            urllib.parse.quote_plus(market)
            for market in _config["sports"][sport]["markets"]
        ]
    )
    return _config["get_event_url"].format(id, markets)


def get_market_kind(market_id: str) -> MarketKind:
    for s in _config["sports"].values():
        kind = s["markets"].get(market_id)
        if kind:
            return MarketKind[kind]
    raise Exception(f"Unable to find kind for id {market_id} fox_bets")
