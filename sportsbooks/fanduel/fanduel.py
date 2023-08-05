import dataclasses
import logging
from datetime import datetime
from typing import Optional

import requests

from datastructures.event import Event
from datastructures.market import Market
from datastructures.selection import Selection
from sportsbooks.fanduel import config

log = logging.getLogger(__name__)


# this works.
# get event
# "https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak=FhMFpcPWXMeyZxOx&eventId=32530968"

# get events
# "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page?page=CUSTOM&customPageId=pga&_ak=FhMFpcPWXMeyZxOx&timezone=America/New_York"

# get events by sport
# https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page?page=SPORT&eventTypeId=1&_ak=FhMFpcPWXMeyZxOx&timezone=America/New_York
# eventTypeId=1 : SOCCER
# eventTypeId=7511 : BASEBALL


def _get_event(url: str):
    log.info(f"Getting event for {url}.")
    res = requests.get(url)

    if res.status_code != 200:
        log.error(
            f"unable to _get_events status_code: {res.status_code} {url},"
            f" text: {res.text}"
        )
        return

    return res.json()


def _parse_events(j) -> list[Event]:
    events = []
    log.debug(j["attachments"].keys())
    for event in j["attachments"]["events"].values():
        log.debug(event.items())
        id = str(event["eventId"])
        events.append(
            Event(
                id,
                event["name"],
                config.get_sport(str(event["eventTypeId"])),
                config.get_date(event["openDate"]),
                config.get_event_url(id),
            )
        )
    log.debug(events)
    return events


def get_events() -> list[Event]:
    log.info("Getting events.")
    events = []
    for url in config.get_events_urls():
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

    return []
    # return _parse_markets(event)
