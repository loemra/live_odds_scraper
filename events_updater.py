from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection
import database.events_database as events_database
import database.translaters.translater as translater
import fox_bets.fox_bets as fox_bets
from datetime import datetime
import uuid
from collections.abc import Callable
from functools import partial


def _make_unified_id() -> str:
    return uuid.uuid4().hex


def _prompt_for_match(sportsbook_thing, unified_things: list):
    print("\n\nMATCHING:")
    print(f"\t\t{sportsbook_thing}")

    for cnt, unified_thing in enumerate(unified_things):
        print(f"Option {cnt+1}:\t{unified_thing}")

    print("\nEnter the option to match or 0 for none of the above.")

    choice = int(input())
    if choice < 0 or choice > len(unified_things):
        print("INVALID... RETRYING")
        return _prompt_for_match(sportsbook_thing, unified_things)

    if choice == 0:
        return None

    return unified_things[choice - 1]


# EVENTS
def _static_translate_event(sportsbook: str, event: EventMetadata) -> EventMetadata:
    sport_translater = translater.get_sport_translater(sportsbook)
    if event.sport not in sport_translater:
        raise f"_translate_event {sportsbook}, {event}\nUnable to find sport in sports_translater"

    event.sport = sport_translater[event.sport]
    return event


def _maybe_match_event(
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


def _unify_event(sportsbook: str, event: EventMetadata) -> EventMetadata:
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


# MARKETS
def _static_translate_market(sportsbook: str, market: MarketMetadata) -> MarketMetadata:
    market_translater = translater.get_market_translater(sportsbook)
    if market.code not in market_translater:
        raise Exception(
            f"_translate_market {sportsbook}, {market}\nUnable to find market in"
            " market_translater"
        )

    market.code = market_translater[market.code]
    return market


def _maybe_match_market(
    sportsbook_market: MarketMetadata, unified_markets: list[MarketMetadata]
) -> MarketMetadata | None:
    if len(unified_markets) == 0:
        return None

    for unified_market in unified_markets:
        if sportsbook_market.code == unified_market.code:
            return unified_market

    return None


def _unify_market(sportsbook: str, sportsbook_market: MarketMetadata) -> MarketMetadata:
    # TODO: I think markets can be translated fully statically, no dynamic unification needed.
    # If so get rid of this function and update events_database.
    return MarketMetadata(sportsbook_market.code)


# PUBLIC
def update_events(
    sportsbook: str,
    sportsbook_get_events: Callable[[datetime], list[EventMetadata]],
    sportsbook_get_odds: Callable[[str, str], list[Market]],
):
    for original_event in sportsbook_get_events(datetime.today()):
        translated_event = _static_translate_event(sportsbook, original_event)
        unified_event = events_database.match_or_register_event(
            partial(_maybe_match_event, translated_event),
            partial(_unify_event, sportsbook, translated_event),
        )
        translater.maybe_register_event(sportsbook, original_event.id, unified_event.id)

        # must use original sportsbook version of the sport here.
        markets = sportsbook_get_odds(original_event.id, original_event.sport)
        for market in markets:
            market.metadata = _static_translate_market(sportsbook, market.metadata)
            market.metadata = events_database.match_or_register_market(
                unified_event.id,
                partial(_maybe_match_market, market.metadata),
                partial(_unify_market, sportsbook, market.metadata),
            )


# SPORTSBOOKS
update_events("fox_bets", fox_bets.get_events, fox_bets.get_odds)
