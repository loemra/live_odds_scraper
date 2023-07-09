import logging
from datetime import datetime

import requests

from datastructures.event import Event
from datastructures.market import MarketKind
from datastructures.selection import Selection
from sportsbooks.bovada import config


def _setup_logger():
    logging.basicConfig(filename="logs/root.log")
    logger = logging.getLogger("bovada")
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
            f"unable to _get_prematch_events status_code: {res.status_code},"
            f" text: {res.text}"
        )
        return

    return res.json()


def _parse_events(j) -> list[Event]:
    events = []
    for league in j:
        for event in league["events"]:
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


def _parse_odds(j) -> list[Selection]:
    selections = []
    for league in j:
        for event in league["events"]:
            for display_group in event["displayGroups"]:
                for market in display_group["markets"]:
                    market_id = market["marketTypeId"]
                    if (
                        market_id not in config.get_markets()
                        or not market["period"]["main"]
                    ):
                        continue
                    market_kind = config.get_market_kind(market_id)

                    if market_kind is MarketKind.OVER_UNDER:
                        _logger.debug(
                            f"{event['description']}, {market['id']}, "
                        )
                        if market["id"] != "G-2W-OU.Total Goals O/U.100":
                            continue

                    link = "0"
                    for selection in market["outcomes"]:
                        id = selection["id"]
                        name = selection["name"]
                        if market_kind is MarketKind.OVER_UNDER:
                            handicap = selection["price"].get("handicap")
                            if not handicap:
                                raise Exception(
                                    f"no handicap for over_under @ {market_id},"
                                    f" {id} {event}"
                                )
                            link = handicap

                        odds = float(selection["price"]["decimal"])
                        selections.append(
                            Selection(id, name, link, market_id, odds)
                        )
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
