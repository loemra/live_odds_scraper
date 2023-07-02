import json


def _get_config():
    with open("bovada/config.json", "r") as f:
        return json.load(f)


_config = _get_config()


def get_events_urls() -> list[str]:
    event_urls = []
    for sport in _config["url_sports"]:
        event_urls.append(_config["get_events_url"].format(sport))
    return event_urls


def get_event_url(link: str) -> str:
    return _config["get_event_url"].format(link)


def get_markets(sport: str) -> list[str]:
    return _config["sports"][sport]["markets"]


def get_headers() -> dict[str, str]:
    return _config["headers"]
