import dataclasses
import logging
from datetime import datetime
from typing import Optional

import requests

from datastructures.event import Event
from datastructures.market import Market
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
                    config.get_sport(event["sport"]),
                    datetime.fromtimestamp(event["startTime"] / 1000),
                    config.get_event_url(event["link"]),
                )
            )
    return events


def _parse_selection(m, market: Market) -> list[Market]:
    link = {}

    for s in m["outcomes"]:
        selection = Selection(
            s["id"],
            s["description"],
            s["price"].get("decimal"),
        )

        if "handicap" in s["price"]:
            if "handicap2" in s["price"]:
                continue
            if s["price"]["handicap"] not in link:
                link[s["price"]["handicap"]] = dataclasses.replace(market)
            link[s["price"]["handicap"]].selection.append(selection)
        else:
            if "0" not in link:
                link["0"] = dataclasses.replace(market)
            link["0"].selection.append(selection)

    return [m for m in link.values()]


def _parse_market(m, sport: str) -> Optional[Market]:
    if not config.is_market(m["marketTypeId"]):
        return None

    try:
        return Market(
            m["id"],
            config.get_name(sport, m["marketTypeId"]),
            config.get_kind(sport, m["marketTypeId"]),
            config.get_period(sport, m["period"]["abbreviation"]),
        )
    except Exception as err:
        _logger.error(err)


def _parse_markets(e) -> list[Market]:
    markets = []
    for league in e:
        for event in league["events"]:
            sport = event["sport"]
            for display_group in event["displayGroups"]:
                for m in display_group["markets"]:
                    market = _parse_market(m, sport)
                    if not market:
                        continue
                    markets.extend(_parse_selection(m, market))

    return markets


def get_events() -> list[Event]:
    events = []
    for url in config.get_events_urls():
        event = _get_event(url)
        if not event:
            continue
        events.extend(_parse_events(event))
    return events


def get_markets(url: str) -> list[Market]:
    event = _get_event(url)
    if not event:
        return []

    return _parse_markets(event)
