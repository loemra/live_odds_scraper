import logging
from datetime import datetime

import requests

from datastructures.event import EventMetadata
from datastructures.market import Market, MarketKind, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from sportsbooks.bovada import config


def _setup_logger():
    logging.basicConfig(filename="logs/root.log", force=True)
    logger = logging.getLogger("bovada")
    logger.propagate = False
    fh = logging.FileHandler("logs/bovada.log")
    fh.setLevel(logging.INFO)
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


def _parse_events(j) -> list[EventMetadata]:
    events = []
    for league in j:
        for event in league["events"]:
            events.append(
                EventMetadata(
                    event["id"],
                    event["description"],
                    event["sport"],
                    datetime.fromtimestamp(event["startTime"] / 1000),
                    config.get_event_url(event["link"]),
                )
            )
    return events


def _parse_over_under_odds(market: Market, outcomes):
    # linked by handicap
    links = {}
    for outcome in outcomes:
        id = outcome["id"]
        handicap = outcome["price"].get("handicap")
        description = outcome["description"]
        name = f"{description} {handicap}"
        odds = {"bovada": float(outcome["price"]["decimal"])}
        market.selection[id] = Selection(SelectionMetadata(id, name), odds)

        if not links[handicap]:
            links[handicap] = []
        links[handicap].append(id)

    market.linked = list(links.values())


def _parse_yes_no_odds(market: Market, outcomes):
    # no links.
    for outcome in outcomes:
        id = outcome["id"]
        handicap = outcome["price"].get("handicap")
        description = outcome["description"]
        name = f"{description} {handicap}"
        odds = {"bovada": float(outcome["price"]["decimal"])}
        market.selection[id] = Selection(SelectionMetadata(id, name), odds)

    market.linked = [[id for id in market.selection]]


def _parse_team_name_odds(market: Market, outcomes):
    # no links.
    for outcome in outcomes:
        id = outcome["id"]
        handicap = outcome["price"].get("handicap")
        description = outcome["description"]
        name = f"{description} {handicap}"
        odds = {"bovada": float(outcome["price"]["decimal"])}
        market.selection[id] = Selection(SelectionMetadata(id, name), odds)

    market.linked = [[id for id in market.selection]]


def _parse_odds(j) -> list[Market]:
    markets = []
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
                    m = Market(MarketMetadata(market_id, market_kind))

                    if market_kind == MarketKind.OVER_UNDER:
                        if market["id"][-1] != "0":
                            continue
                        _parse_over_under_odds(m, market["outcomes"])
                    elif market_kind == MarketKind.YES_NO:
                        _parse_yes_no_odds(m, market["outcomes"])
                    elif market_kind == MarketKind.TEAM_NAME:
                        _parse_team_name_odds(m, market["outcomes"])

                    markets.append(m)
    return markets


def get_events(_: datetime) -> list[EventMetadata]:
    events = []
    for url in config.get_events_urls():
        event = _get_event(url)
        if not event:
            continue
        events.extend(_parse_events(event))
    return events


def get_odds(url: str) -> list[Market]:
    event = _get_event(url)
    if not event:
        return []
    return _parse_odds(event)


def get_updates():
    pass


def register_for_live_odds_updates(
    event_id: str, markets: list[MarketMetadata]
):
    pass
