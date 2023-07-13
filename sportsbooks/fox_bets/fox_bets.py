import logging
from datetime import datetime, timedelta
from timeit import timeit

import requests

from datastructures.event import Event
from datastructures.market import MarketKind
from datastructures.selection import Selection
from sportsbooks.fox_bets import config


def _setup_logger():
    logger = logging.getLogger("fox_bets")
    logger.propagate = False
    fh = logging.FileHandler("logs/fox_bets.log")
    fh.setLevel(logging.DEBUG)
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
        market_kind = config.get_market_kind(market_id)

        for selection in market["selection"]:
            id = selection["id"]
            try:
                odds = float(selection["odds"]["dec"])
            except ValueError:
                continue
            link = "0"
            if market_kind is MarketKind.OVER_UNDER:
                link = market["subtype"]
            selections.append(
                Selection(id, selection["name"], link, market_id, odds)
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
    time = timeit(lambda: _get_event(url), number=1)
    _logger.info(f"time for get request {time} seconds")
    event = _get_event(url)

    time = timeit(lambda: _parse_odds(event), number=1)
    _logger.info(f"time for parse {time} seconds")
    return _parse_odds(event)
    return _parse_odds(_get_event(url))
