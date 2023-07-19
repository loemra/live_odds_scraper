import json
import logging
from datetime import datetime, timedelta
from typing import Callable

import requests

from datastructures.event import Event
from datastructures.market import Market, MarketKind
from datastructures.selection import Selection
from sportsbooks.fox_bets import config


def _setup_logger():
    logger = logging.getLogger("fox_bets")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("logs/fox_bets.log")
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
            # TODO: handle live events.
            if date < datetime.now():
                continue

            events.append(
                Event(
                    event["id"],
                    event["name"],
                    event["sport"],
                    date,
                    config.get_event_url(event["id"]),
                )
            )
    return events


def _modular_market_parser(
    m,
    market: Market,
    skip_selection: Callable[[dict, dict], bool] = lambda *_: False,
    make_name: Callable[[dict, dict], str] = lambda _, s: s["name"],
    make_link: Callable[[dict, dict], str] = lambda *_: "0",
) -> list[Selection]:
    selections = []
    for selection in m["selection"]:
        if skip_selection(m, selection):
            continue

        id = selection["id"]
        name = make_name(m, selection)
        link = make_link(m, selection)
        try:
            odds = float(selection["odds"]["dec"])
        except ValueError:
            continue
        selections.append(Selection(id, name, link, market, odds))

    return selections


def _parse_market(m, sport: str) -> list[Selection]:
    id = m["type"]
    if not config.is_market(id):
        return []
    kind = config.get_market_kind(id)
    # TODO: config.get_market_period(m["period"], m["periodMarket"])
    period = m["period"] if m["periodMarket"] else "full"

    market = Market(id, period, kind)
    _logger.info(market)

    if kind is MarketKind.OVER_UNDER and sport == "SOCCER":
        return _modular_market_parser(
            m, market, make_link=lambda m, _: m["subtype"]
        )

    return _modular_market_parser(m, market)


def _parse_odds(j) -> list[Selection]:
    selections = []
    sport = j["sport"]
    for market in j["markets"]:
        selections.extend(_parse_market(market, sport))
    return selections


def get_events() -> list[Event]:
    events = []
    for date in [datetime.today() + timedelta(i) for i in range(10)]:
        for event_url in config.get_events_urls(date):
            events.extend(_parse_events(_get_event(event_url)))
    return events


def get_odds(url: str) -> list[Selection]:
    event = _get_event(url)
    print(url)
    with open("sportsbooks/fox_bets/data/events.json", "a") as f:
        json.dump(event, f)
    return _parse_odds(event)
