import logging
from datetime import datetime, timedelta

import requests

from datastructures.event import Event
from datastructures.selection import Selection
from sportsbooks.fox_bets import config


def _setup_logger():
    logging.basicConfig(filename="logs/root.log")
    logger = logging.getLogger("fox_bets")
    logger.propagate = False
    fh = logging.FileHandler("logs/fox_bets.log")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s @ %(lineno)s == %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


_logger = _setup_logger()


def _get_event(url: str):
    result = requests.get(url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_event(): status code = {result.status_code}, url ="
            f" {url}, text = {result.text}"
        )
    return result.json()


def _parse_events(j) -> list[Event]:
    events = []
    for league in j:
        for event in league["event"]:
            date = datetime.fromtimestamp(float(event["eventTime"]) / 1000)
            events.append(
                Event(
                    event["id"],
                    event["name"],
                    event["sport"],
                    date,
                    config.get_event_url(event["id"], event["sport"]),
                )
            )
    return events


def _parse_odds(j) -> list[Selection]:
    selections = []
    for market in j["markets"]:
        market_id = market["type"]

        ids = []
        for selection in market["selection"]:
            id = selection["id"]
            ids.append(id)
            try:
                odds = float(selection["odds"]["dec"])
            except ValueError:
                continue
            selections.append(
                Selection(id, selection["name"], "0", market_id, odds)
            )
    return selections


# gets all upcoming events for fox_bets and returns: event name, sport, time, and fox_bet_event_id.
def get_events() -> list[Event]:
    events = []
    for date in [datetime.today() + timedelta(i) for i in range(3)]:
        for event_url in config.get_events_urls(date):
            events.extend(_parse_events(_get_event(event_url)))
    return events


# gets initial odds for an upcoming event given fox_bet_event_id.
def get_odds(url: str) -> list[Selection]:
    return _parse_odds(_get_event(url))
