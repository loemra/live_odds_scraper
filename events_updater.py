from datastructures.event import EventMetadata
from datastructures.market import Market
import database.events_database as events_database
import database.translater as translater
import fox_bets.fox_bets as fox_bets
from datetime import datetime
import uuid
from collections.abc import Callable


def _make_unified_id() -> str:
    return uuid.uuid4().hex


def _prompt_for_unification(sportsbook: str, event: EventMetadata) -> EventMetadata:
    print(f"\n\nUNIFYING {sportsbook} event:")
    print(f"\t\t{event}\n")

    print("enter comma separated fields you would like to update:")
    fields = input().split(",")

    name = event.name
    sport = event.sport
    date = event.date

    if "name" in fields:
        print("\nEnter unified name:")
        name = input()

    if "sport" in fields:
        print("\nEnter unified sport:")
        sport = input()

    if "date" in fields:
        print("\nEnter unified date:")
        date = datetime.fromtimestamp(input())

    return EventMetadata(_make_unified_id(), name, sport, date)


def _prompt_for_match(
    sportsbook_event: EventMetadata, unified_events: list[EventMetadata]
) -> EventMetadata | None:
    print("\n\nMATCHING:")
    print(f"\t\t{sportsbook_event}")

    for cnt, unified_event in enumerate(unified_events):
        print(f"Option {cnt+1}:\t{unified_event}")

    print("\nEnter the option to match or 0 for none of the above.")

    choice = int(input())
    if choice < 0 or choice > len(unified_events):
        print("INVALID... RETRYING")
        return _maybe_match(sportsbook_event, unified_events)

    if choice == 0:
        return None

    return unified_events[choice - 1]


def _maybe_match(
    sportsbook_event: EventMetadata, unified_events: list[EventMetadata]
) -> EventMetadata | None:
    if len(unified_events) == 0:
        return None

    # some basic logic to try to automate a little bit.
    some_match_date = False
    for unified_event in unified_events:
        if sportsbook_event.date == unified_event.date:
            some_match_date = True
        if sportsbook_event.name == unified_event.name:
            return unified_event
    if not some_match_date:
        return None

    return _prompt_for_match(sportsbook_event, unified_events)


def _match_or_register_events_database(
    sportsbook: str, event: EventMetadata
) -> EventMetadata:
    with events_database.lock:
        unified_events = events_database.get_events()

        unified_event = _maybe_match(event, unified_events)

        if not unified_event:
            # event has not been registered yet.
            unified_event = _prompt_for_unification(sportsbook, event)
            events_database.register_new_event(unified_event)

        return unified_event


def _match_or_register_translater(
    sportsbook: str, sportsbook_event_id: str, unified_id: str
):
    with translater.lock:
        event_id_translater = translater.get_event_id_translater(sportsbook)

        if sportsbook_event_id in event_id_translater:
            return

        translate = {sportsbook: sportsbook_event_id}
        translater.create_event(unified_id, translate)


def _translate_event(sportsbook: str, event: EventMetadata) -> EventMetadata:
    sport_translater = translater.get_sport_translater(sportsbook)
    if event.sport in sport_translater:
        event.sport = sport_translater[event.sport]

    return event


def _translate_market(sportsbook: str, market: Market) -> Market:
    pass


def update_events(
    sportsbook: str,
    sportsbook_get_events: Callable[[datetime], list[EventMetadata]],
    sportsbook_get_odds: Callable[[str, str], list[Market]],
):
    for event in sportsbook_get_events(datetime.today()):
        unified_event = _match_or_register_events_database(
            sportsbook, _translate_event(sportsbook, event)
        )
        _match_or_register_translater(sportsbook, event.id, unified_event.id)

        markets = sportsbook_get_odds(event.id, event.sport)
        for market in markets:
            unified_market = _translate_market(market)


# def update_odds():


# SPORTSBOOKS
update_events("fox_bets", fox_bets.get_events, fox_bets.get_odds)


# fox_bets.get_odds()
