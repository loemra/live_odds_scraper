import logging
from datetime import datetime, timedelta
from typing import Optional

import requests

from datastructures.event import Event
from datastructures.market import Market
from datastructures.selection import Selection
from sportsbooks.fox_bets import config

log = logging.getLogger(__name__)


def _get_event(url: str):
    log.info(f"Getting event for {url}.")
    result = requests.get(url)
    if not result.status_code == 200:
        log.error(
            f"fox_bets: _get_event(): status code: {result.status_code}, url ="
            f" {url}, text = {result.text}"
        )
        return
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


def _parse_selection(m, market: Market):
    selection = []
    for s in m["selection"]:
        selection.append(
            Selection(
                s["id"],
                s["name"],
                s["odds"]["dec"] if s["odds"]["dec"] != "-" else None,
            )
        )
    market.selection = selection


def _parse_market(m, sport: str) -> Optional[Market]:
    if not config.is_market(m["type"]):
        return None

    try:
        return Market(
            m["id"],
            config.get_name(sport, m["type"]),
            config.get_kind(sport, m["type"]),
            config.get_period(
                sport, m["period"] if m["periodMarket"] else None
            ),
            line=m.get("line"),
        )
    except Exception:
        log.exception(f"Something went wrong parsing market for {sport}\n{m}")


def _parse_markets(e) -> list[Market]:
    markets = []
    sport = e["sport"]
    for m in e["markets"]:
        market = _parse_market(m, sport)
        if not market:
            continue
        _parse_selection(m, market)
        markets.append(market)
    return markets


def get_events() -> list[Event]:
    log.info("Getting events.")
    events = []
    for date in [datetime.today() + timedelta(i) for i in range(10)]:
        for url in config.get_events_urls(date):
            event = _get_event(url)
            if not event:
                continue
            events.extend(_parse_events(event))
    return events


def get_markets(url: str) -> list[Market]:
    log.info(f"Getting markets for {url}.")
    event = _get_event(url)
    if not event:
        return []

    return _parse_markets(event)
