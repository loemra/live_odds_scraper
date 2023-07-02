from datetime import datetime

import requests

from bovada import config
from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata


def _get_event(url: str):
    res = requests.get(url, headers=config.get_headers())

    if res.status_code != 200:
        raise Exception(f"unable to _get_prematch_events status_code: {res.status_code}, text: {res.text}")

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


def _parse_odds(j) -> list[Market]:
    markets = []
    for league in j:
        for event in league["events"]:
            for market in event["markets"]:
                m = Market(MarketMetadata(market["marketTypeId"]))
                for outcome in market["outcomes"]:
                    m.selection[outcome["id"]] = Selection(
                        SelectionMetadata(outcome["id"], outcome["description"]),
                        {"bovada": float(outcome["price"]["decimal"])},
                    )
                markets.append(m)
    return markets


def get_events(_: datetime) -> list[EventMetadata]:
    events = []
    for url in config.get_events_urls():
        events.extend(_parse_events(_get_event(url)))
    return events


def get_odds(url: str) -> list[Market]:
    return _parse_odds(_get_event(url))


def get_updates():
    pass


def register_for_live_odds_updates(event_id: str, markets: list[MarketMetadata]):
    pass
