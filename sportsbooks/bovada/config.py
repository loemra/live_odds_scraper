import json

from datastructures.market import MarketKind


def _get_config():
    with open("sportsbooks/bovada/config.json", "r") as f:
        return json.load(f)


_config = _get_config()


def get_events_urls() -> list[str]:
    event_urls = []
    for sport in _config["url_sports"]:
        event_urls.append(_config["get_events_url"].format(sport))
    return event_urls


def get_event_url(link: str) -> str:
    return _config["get_event_url"].format(link)


def is_market(market: str) -> bool:
    for s in _config["sports"].values():
        if market in s["markets"].keys():
            return True
    return False


def get_market_kind(id: str) -> MarketKind:
    for s in _config["sports"].values():
        kind = s["markets"].get(id)
        if kind:
            return MarketKind[kind]
    raise Exception(f"Unable to find kind for id {id} bovada")


def get_headers() -> dict[str, str]:
    return _config["headers"]
