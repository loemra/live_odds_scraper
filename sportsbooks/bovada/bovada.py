import logging
from datetime import datetime
from typing import Callable

import requests

from datastructures.event import Event
from datastructures.market import Market, MarketKind
from datastructures.selection import Selection
from sportsbooks.bovada import config


def _setup_logger():
    logging.basicConfig()
    logger = logging.getLogger("bovada")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    fh = logging.FileHandler("logs/bovada.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s @ %(lineno)s == %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


_logger = _setup_logger()


def _get_event(url: str):
    res = requests.get(url, headers=config.get_headers())

    if res.status_code != 200:
        _logger.error(
            f"unable to _get_events status_code: {res.status_code} {url},"
            f" text: {res.text}"
        )
        return

    return res.json()


def _parse_events(j) -> list[Event]:
    events = []
    for league in j:
        for event in league["events"]:
            # TODO: handle live events
            if event["live"]:
                continue
            events.append(
                Event(
                    event["id"],
                    event["description"],
                    event["sport"],
                    datetime.fromtimestamp(event["startTime"] / 1000),
                    config.get_event_url(event["link"]),
                )
            )
    return events


def _modular_market_parser(
    m,
    market: Market,
    skip_selection: Callable[[dict, dict], bool] = lambda *_: False,
    make_selection_name: Callable[[dict, dict], str] = lambda _, s: s[
        "description"
    ],
    make_link: Callable[[dict, dict], str] = lambda *_: "0",
) -> list[Selection]:
    selections = []
    for selection in m["outcomes"]:
        if skip_selection(m, selection):
            continue

        id = selection["id"]
        name = make_selection_name(m, selection)
        link = make_link(m, selection)
        odds = float(selection["price"]["decimal"])

        selections.append(Selection(id, name, link, market, odds))

    return selections


def _parse_market(m, sport: str) -> list[Selection]:
    id = m["marketTypeId"]
    if not config.is_market(id):
        return []
    kind = config.get_market_kind(id)
    period = m["period"]["description"]

    market = Market(id, period, kind)
    _logger.info(market)

    # deal with special cases.
    if kind is MarketKind.OVER_UNDER and sport == "SOCC":
        if id != "G-2W-OU.Total Goals O/U.100":
            return []

        return _modular_market_parser(
            m,
            market,
            skip_selection=lambda _, s: "handicap2" in s["price"],
            make_selection_name=lambda _, s: f"{s['description']} {s['price']['handicap']}",
            make_link=lambda _, s: s["price"]["handicap"],
        )
    if kind is MarketKind.OVER_UNDER and sport == "TENN":
        pass

    # default
    return _modular_market_parser(m, market)


def _parse_odds(j) -> list[Selection]:
    selections = []
    for league in j:
        for event in league["events"]:
            sport = event["sport"]

            for display_group in event["displayGroups"]:
                for market in display_group["markets"]:
                    selections.extend(_parse_market(market, sport))

    return selections


def get_events() -> list[Event]:
    events = []
    for url in config.get_events_urls():
        event = _get_event(url)
        if not event:
            continue
        events.extend(_parse_events(event))
    return events


def get_odds(url: str) -> list[Selection]:
    event = _get_event(url)
    if not event:
        return []

    return _parse_odds(event)
