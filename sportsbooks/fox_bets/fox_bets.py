from datetime import datetime, timedelta

import requests

from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from sportsbooks.fox_bets import config


def _parse_events(j) -> list[EventMetadata]:
    events = []
    for league in j:
        for event in league["event"]:
            date = datetime.fromtimestamp(float(event["eventTime"]) / 1000)
            events.append(
                EventMetadata(
                    event["id"],
                    event["name"],
                    event["sport"],
                    date,
                    config.get_event_url(event["id"], event["sport"]),
                )
            )
    return events


def _parse_odds(j) -> list[Market]:
    markets = []
    for market in j["markets"]:
        if (
            market.get("mostBalanced") is not None
            and market["mostBalanced"] == False
        ):
            continue
        market_id = market["type"]
        metadata = MarketMetadata(market_id, config.get_market_kind(market_id))
        m = Market(metadata)
        for selection in market["selection"]:
            id = selection["id"]
            try:
                odds = {"fox_bets": float(selection["odds"]["dec"])}
            except ValueError:
                odds = {}
            m.selection[id] = Selection(
                SelectionMetadata(id, selection["name"]), odds
            )
        markets.append(m)
    return markets


def _get_events(events_url: str):
    result = requests.get(events_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_events(): status code = {result.status_code}, url"
            f" = {events_url}, text = {result.text}"
        )
    return result.json()


def _get_event(event_url: str):
    result = requests.get(event_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_event(): status code = {result.status_code}, url ="
            f" {event_url}, text = {result.text}"
        )
    return result.json()


# gets all upcoming events for fox_bets and returns: event name, sport, time, and fox_bet_event_id.
def get_events(_: datetime) -> list[EventMetadata]:
    events = []
    for date in [datetime.today() + timedelta(i) for i in range(3)]:
        for event_url in config.get_events_urls(date):
            events.extend(_parse_events(_get_events(event_url)))
    return events


# gets initial odds for an upcoming event given fox_bet_event_id.
def get_odds(url: str) -> list[Market]:
    return _parse_odds(_get_event(url))
