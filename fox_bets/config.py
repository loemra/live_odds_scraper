import json
from datetime import datetime
from typing import Tuple
import urllib.parse
from datastructures.market import MarketMetadata


def _get_config():
    with open("fox_bets/config.json", "r") as f:
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


def get_send_alive() -> str:
    return _config["sockets"]["send_alive"]


def get_url_and_auth_payload() -> Tuple[str, list[str]]:
    return (_config["sockets"]["url"], _config["sockets"]["auth_payload"])


def get_subscribe_payload(event_id: str, markets: list[MarketMetadata]) -> str:
    return _config["sockets"]["subscribe_payload"].format(
        event_id, ",".join([market.code for market in markets])
    )


def get_ri_odds(ri: int) -> float:
    return float(_config["odds"][ri]["decimal"])
