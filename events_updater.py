import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial

from thefuzz import fuzz, process

import database.events_database as events_database
import database.translaters.translater as translater
import fox_bets.fox_bets as fox_bets
from bovada import bovada
from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from datastructures.update import Update


def _setup_logger():
    logging.basicConfig(level=logging.DEBUG, force=True)
    logger = logging.getLogger("events_updater")
    logger.propagate = False
    fh = logging.FileHandler("logs/events_updater.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s @ %(filename)s:%(funcName)s:%(lineno)s == %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


_logger = _setup_logger()


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

    relevant_events = [
        event for event in unified_events if abs((sportsbook_event.date - event.date).total_seconds()) < 3600
    ]
    if not relevant_events:
        return None

    best_matches = process.extractBests(
        sportsbook_event, relevant_events, lambda e: e.name, fuzz.token_sort_ratio, score_cutoff=75
    )

    if not best_matches:
        res = process.extract(sportsbook_event, relevant_events, lambda e: e.name, fuzz.token_sort_ratio)
        _logger.debug(f"successful no match: {sportsbook_event}, {res}")
        return None
    if len(best_matches) == 1:
        _logger.debug(f"successful match: {sportsbook_event}, {best_matches}")
        return best_matches[0][0]

    _logger.debug(f"{sportsbook_event} has multiple best matches {best_matches}")

    return _prompt_for_match(sportsbook_event, relevant_events)


def _unify_event(sportsbook: str, event: EventMetadata) -> EventMetadata:
    unified_name = translater.sportsbook_to_unified_event_name(sportsbook, event.name)
    if not unified_name:
        unified_name = event.name

    # sport already unified as it is static.

    return EventMetadata(_make_unified_id(), event.name, event.sport, event.date)


# SELECTION


def _maybe_match_selection(
    sportsbook: str, sportsbook_selection: SelectionMetadata, unified_selctions: list[SelectionMetadata]
) -> SelectionMetadata | None:
    if len(unified_selctions) == 0:
        return None

    # special case for tie / draw.
    def custom_scorer(query, choice):
        if query.lower() == "tie" or query.lower() == "draw":
            return max(fuzz.token_sort_ratio("tie", choice), fuzz.token_sort_ratio("draw", choice))
        return fuzz.token_sort_ratio(query, choice)

    best_matches = process.extractBests(
        sportsbook_selection, unified_selctions, lambda e: e.name, custom_scorer, score_cutoff=79
    )

    if not best_matches:
        res = process.extract(sportsbook_selection, unified_selctions, lambda e: e.name, fuzz.token_sort_ratio)
        _logger.debug(f"successful no match: {sportsbook_selection}, {res}")
        return None
    if len(best_matches) == 1:
        _logger.debug(f"successful match: {sportsbook_selection}, {best_matches}")
        return best_matches[0][0]

    _logger.debug(f"{sportsbook_selection} has multiple best matches {best_matches}")

    return _prompt_for_match(sportsbook_selection, unified_selctions)


def _unify_selection(sportsbook: str, selection: SelectionMetadata) -> SelectionMetadata:
    unified_name = translater.sportsbook_to_unified_selection_name(sportsbook, selection.name)
    if not unified_name:
        unified_name = selection.name
        if "{" in selection.name:
            unified_name = unified_name.split("{")[0].strip()
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
        translater.maybe_register_selection_name(sportsbook, selection.metadata.name, unified_selection.name)

    events_database.update_event_odds(
        Update(unified_event_id, unified_market_id, unified_selection_id, sportsbook, selection.odds[sportsbook])
    )


def _update_market(sportsbook: str, unified_event_id: str, market: Market):
    unified_market_id = translater.sportsbook_to_unified_market_id(sportsbook, market.metadata.id)
    if not unified_market_id:
        _logger.warning(f"unable to translate market {market.metadata} for {sportsbook}")
        return
    unified_market = MarketMetadata(unified_market_id, market.metadata.kind)
    events_database.maybe_register_market(unified_event_id, unified_market)

    for selection in market.selection.values():
        _update_selection(sportsbook, unified_event_id, unified_market_id, selection)


def _update_event(sportsbook: str, get_odds: Callable[[str], list[Market]], event: EventMetadata):
    unified_event_id = translater.sportsbook_to_unified_event_id(sportsbook, event.id)
    if not unified_event_id:
        unified_sport = translater.sportsbook_to_unified_sport(sportsbook, event.sport)
        if not unified_sport:
            _logger.error(f"unable to find unified sport {event.sport} for {sportsbook}")
            return
        event.sport = unified_sport
        unified_event = events_database.match_or_register_event(
            partial(_maybe_match_event, event),
            partial(_unify_event, sportsbook, event),
        )
        unified_event_id = unified_event.id
        translater.maybe_register_event_id(sportsbook, event.id, unified_event_id)
        translater.maybe_register_event_name(sportsbook, event.name, unified_event.name)

    if event.url is None:
        _logger.error(f"no event url for {event}")
        return
    markets = get_odds(event.url)
    for market in markets:
        _update_market(sportsbook, unified_event_id, market)


def update_events(
    sportsbook: str,
    get_events: Callable[[datetime], list[EventMetadata]],
    get_odds: Callable[[str], list[Market]],
):
    for event in get_events(datetime.today() + timedelta(0)):
        _update_event(sportsbook, get_odds, event)


# SPORTSBOOKS
update_events("fox_bets", fox_bets.get_events, fox_bets.get_odds)
update_events("bovada", bovada.get_events, bovada.get_odds)
