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
    unified_sport = translater.translate_sport(sportsbook, event.sport)
    if not unified_sport:
        raise f"_translate_event {sportsbook}, {event}\nUnable to find sport in sports_translater"

    event.sport = unified_sport
    return event


def _maybe_match_event(
    sportsbook: str,
    sportsbook_event: EventMetadata,
    unified_events: list[EventMetadata],
) -> EventMetadata | None:
    if len(unified_events) == 0:
        return None

    # some basic logic to try to automate a little bit.
    unified_id = translater.translate_event_id(sportsbook, sportsbook_event.id)

    some_match_date = False
    for unified_event in unified_events:
        if sportsbook_event.date == unified_event.date:
            some_match_date = True
        if sportsbook_event.name == unified_event.name:
            return unified_event
        if unified_id == unified_event.id:
            return unified_event
    if not some_match_date:
        return None

    return _prompt_for_match(sportsbook_event, unified_events)


def _unify_event(sportsbook: str, event: EventMetadata) -> EventMetadata:
    return EventMetadata(_make_unified_id(), event.name, event.sport, event.date)
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
    unified_market = translater.translate_market(sportsbook, market.code)
    if not unified_market:
        raise Exception(
            f"_translate_market {sportsbook}, {market}\nUnable to find market in"
            " market_translater"
        )

    market.code = unified_market
    return market


def _maybe_match_market(
    sportsbook_market: MarketMetadata, unified_markets: list[MarketMetadata]
) -> MarketMetadata | None:
    if len(unified_markets) == 0:
        return None

    for unified_market in unified_markets:
        # allowed to do this because code is statically translated before this.
        if sportsbook_market.code == unified_market.code:
            return unified_market

    return None


def _unify_market(sportsbook: str, sportsbook_market: MarketMetadata) -> MarketMetadata:
    # TODO: I think markets can be translated fully statically, no dynamic unification needed.
    # If so get rid of this function and update events_database.
    return sportsbook_market


# SELECTION
def _maybe_match_selection(
    sportsbook: str, sportsbook_selection: Selection, unified_selctions: list[Selection]
) -> Selection | None:
    if len(unified_selctions) == 0:
        return None

    unified_id = translater.get_selection_id_translater(sportsbook).get(
        sportsbook_selection.id
    )
    for selection in unified_selctions:
        if unified_id == selection.id:
            return selection

    return _prompt_for_match(sportsbook_selection, unified_selctions)


def _unify_selection(sportsbook: str, selection: Selection) -> Selection:
    return Selection(_make_unified_id(), selection.name, selection.odds)
    print(f"\n\nUNIFYING {sportsbook} selection:")
    print(f"\t\t{selection}\n")

    print("enter comma separated fields you would like to update:")
    fields = input().split(",")

    name = selection.name

    if "name" in fields:
        print("\nEnter unified name:")
        name = input()

    return Selection(_make_unified_id(), name, selection.odds)


# PUBLIC
def update_events(
    sportsbook: str,
    sportsbook_get_events: Callable[[datetime], list[EventMetadata]],
    sportsbook_get_odds: Callable[[str, str], list[Market]],
):
    for event in sportsbook_get_events(datetime.today()):
        original_sport = event.sport
        translated_event = _static_translate_event(sportsbook, event)
        unified_event = events_database.match_or_register_event(
            partial(_maybe_match_event, sportsbook, translated_event),
            partial(_unify_event, sportsbook, translated_event),
        )
        translater.maybe_register_event(sportsbook, event.id, unified_event.id)

        # must use original sportsbook version of the sport here.
        markets = sportsbook_get_odds(event.id, original_sport)
        for market in markets:
            market.metadata = _static_translate_market(sportsbook, market.metadata)
            market.metadata = events_database.match_or_register_market(
                unified_event.id,
                partial(_maybe_match_market, market.metadata),
                partial(_unify_market, sportsbook, market.metadata),
            )

            for selection in market.selection.values():
                original_id = selection.id
                # no static translations for selection.
                selection = events_database.match_or_register_selection(
                    unified_event.id,
                    market.metadata.code,
                    partial(_maybe_match_selection, sportsbook, selection),
                    partial(_unify_selection, sportsbook, selection),
                )
                translater.maybe_register_selection(
                    sportsbook, original_id, selection.id
                )


# SPORTSBOOKS
update_events("fox_bets", fox_bets.get_events, fox_bets.get_odds)
