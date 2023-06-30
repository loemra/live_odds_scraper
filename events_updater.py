import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial

import database.events_database as events_database
import database.translaters.translater as translater
import fox_bets.fox_bets as fox_bets
from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from datastructures.update import Update


def _make_unified_id() -> str:
    return uuid.uuid4().hex


def _prompt_for_match(sportsbook_thing, unified_things: list):
    print("\n\nMATCHING:")
    print(f"\t\t{sportsbook_thing}")

    for cnt, unified_thing in enumerate(unified_things):
        print(f"Option {cnt+1}:\t{unified_thing}")

    print("\nEnter the option to match or 0 for none of the above.")

    choice = input()
    if not choice:
        return None
    choice = int(choice)
    if choice < 0 or choice > len(unified_things):
        print("INVALID... RETRYING")
        return _prompt_for_match(sportsbook_thing, unified_things)

    if choice == 0:
        return None

    return unified_things[choice - 1]


# EVENTS


def _maybe_match_event(
    sportsbook_event: EventMetadata,
    unified_events: list[EventMetadata],
) -> EventMetadata | None:
    if len(unified_events) == 0:
        return None

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
    unified_name = translater.sportsbook_to_unified_event_name(sportsbook, event.name)
    if not unified_name:
        print(f"\n\nUnify event {event}, input new name:")
        unified_name = input()
        if not unified_name:
            unified_name = event.name
        translater.maybe_register_event_name(sportsbook, event.name, unified_name)

    unified_sport = translater.sportsbook_to_unified_sport(sportsbook, event.sport)
    if not unified_sport:
        raise Exception(f"unable to translate {event.sport} for {sportsbook}")
    return EventMetadata(_make_unified_id(), event.name, unified_sport, event.date)


# MARKETS


def _maybe_match_market(
    sportsbook_market: MarketMetadata, unified_markets: list[MarketMetadata]
) -> MarketMetadata | None:
    if len(unified_markets) == 0:
        return None

    return _prompt_for_match(sportsbook_market, unified_markets)


def _unify_market(sportsbook: str, sportsbook_market: MarketMetadata) -> MarketMetadata:
    unified_id = translater.sportsbook_to_unified_market_id(sportsbook, sportsbook_market.id)
    if not unified_id:
        raise Exception(f"unable to translate market {sportsbook_market.id}")
    return MarketMetadata(unified_id)


# SELECTION
def _maybe_match_selection(
    sportsbook: str, sportsbook_selection: SelectionMetadata, unified_selctions: list[SelectionMetadata]
) -> SelectionMetadata | None:
    if len(unified_selctions) == 0:
        return None

    unified_id = translater.sportsbook_to_unified_selection_id(sportsbook, sportsbook_selection.id)
    for selection in unified_selctions:
        if unified_id == selection.id:
            return selection

    return _prompt_for_match(sportsbook_selection, unified_selctions)


def _unify_selection(sportsbook: str, selection: SelectionMetadata) -> SelectionMetadata:
    unified_name = translater.sportsbook_to_unified_selection_name(sportsbook, selection.name)
    if not unified_name:
        print(f"\n\nUnify selection {selection}, input new name:")
        unified_name = input()
        if not unified_name:
            unified_name = selection.name
        translater.maybe_register_selection_name(sportsbook, selection.name, unified_name)
    return SelectionMetadata(_make_unified_id(), unified_name)


def _update_selection(sportsbook: str, unified_event_id: str, unified_market_id: str, selection: Selection):
    unified_selection_id = translater.sportsbook_to_unified_selection_id(sportsbook, selection.metadata.id)
    if not unified_selection_id:
        unified_selection = events_database.match_or_register_selection(
            unified_event_id,
            unified_market_id,
            partial(_maybe_match_selection, sportsbook, selection.metadata),
            partial(_unify_selection, sportsbook, selection.metadata),
        )
        unified_selection_id = unified_selection.id
        translater.maybe_register_selection_id(sportsbook, selection.metadata.id, unified_selection.id)

    events_database.update_event_odds(
        Update(unified_event_id, unified_market_id, unified_selection_id, sportsbook, selection.odds[sportsbook])
    )


def _update_market(sportsbook: str, unified_event_id: str, market: Market):
    unified_market_id = translater.sportsbook_to_unified_market_id(sportsbook, market.metadata.id)
    if not unified_market_id:
        raise Exception(f"unable to translate market {market.metadata} for {sportsbook}")
    unified_market = MarketMetadata(unified_market_id)
    events_database.maybe_register_market(unified_event_id, unified_market)

    for selection in market.selection.values():
        _update_selection(sportsbook, unified_event_id, unified_market_id, selection)


def _update_event(sportsbook: str, get_odds: Callable[[str, str], list[Market]], event: EventMetadata):
    unified_event_id = translater.sportsbook_to_unified_event_id(sportsbook, event.id)
    if not unified_event_id:
        unified_event = events_database.match_or_register_event(
            partial(_maybe_match_event, event),
            partial(_unify_event, sportsbook, event),
        )
        unified_event_id = unified_event.id
        translater.maybe_register_event_id(sportsbook, event.id, unified_event_id)

    markets = get_odds(event.id, event.sport)
    for market in markets:
        _update_market(sportsbook, unified_event_id, market)


def update_events(
    sportsbook: str,
    get_events: Callable[[datetime], list[EventMetadata]],
    get_odds: Callable[[str, str], list[Market]],
):
    for event in get_events(datetime.today() + timedelta(0)):
        _update_event(sportsbook, get_odds, event)


# SPORTSBOOKS
update_events("fox_bets", fox_bets.get_events, fox_bets.get_odds)
