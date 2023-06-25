import json
from datetime import date


def _get_config():
    with open("fox_bets/config.json", "r") as f:
        return json.load(f)


_config = _get_config()


def get_events_urls() -> list[str]:
    event_urls = []
    today = date.today().strftime(r"%Y-%m-%d")
    for _, event in _config["sports"].items():
        event_urls.append(event["get_events_url"].format(today))
    return event_urls
