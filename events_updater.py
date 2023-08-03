import logging
from typing import Callable

from thefuzz import fuzz, process

from database import db
from datastructures.event import Event
from datastructures.market import Market
from datastructures.selection import Selection

log = logging.getLogger(__name__)


def _prompt_for_match(sportsbook_thing, unified_things: list):
    print(f"\n\nMATCHING:\t{sportsbook_thing}")

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


def _maybe_match_event(
    event: Event, potential_events: list[Event]
) -> Event | None:
    if len(potential_events) == 0:
        return None

    relevant_events = [
        p_event
        for p_event in potential_events
        if abs((event.date - p_event.date).total_seconds()) < 3600
    ]
    if not relevant_events:
        return None

    best_matches = process.extractBests(
        event,
        relevant_events,
        lambda e: e.name,
        fuzz.token_sort_ratio,
        score_cutoff=75,
    )

    if not best_matches:
        res = process.extract(
            event,
            relevant_events,
            lambda e: e.name,
            fuzz.token_sort_ratio,
        )
        log.debug(f"successful no match: {event}, {res}")
        return None
    if len(best_matches) == 1:
        log.debug(f"successful match: {event}, {best_matches}")
        return best_matches[0][0]

    log.debug(f"{event} has multiple best matches {best_matches}")

    return _prompt_for_match(event, relevant_events)


def _maybe_match_selection(
    selection: Selection,
    potential_selections: list[Selection],
) -> Selection | None:
    if len(potential_selections) == 0:
        return None

    # special case for tie / draw and over / under.
    def custom_scorer(query, choice):
        if query.lower() == "tie" or query.lower() == "draw":
            return max(
                fuzz.token_sort_ratio("tie", choice.lower()),
                fuzz.token_sort_ratio("draw", choice.lower()),
            )

        if ("over" in query.lower() or "under" in query.lower()) and (
            "over" in choice.lower() or "under" in choice.lower()
        ):
            if ("over" in query.lower()) == ("under" in choice.lower()):
                return 0
            query = query.lower().replace("over", "").replace("under", "")
            choice = choice.lower().replace("over", "").replace("under", "")

        return fuzz.token_sort_ratio(query, choice)

    best_matches = process.extractBests(
        selection,
        potential_selections,
        lambda e: e.name,
        custom_scorer,
        score_cutoff=85,
    )

    if not best_matches:
        res = process.extract(
            selection,
            potential_selections,
            lambda e: e.name,
            custom_scorer,
        )
        log.debug(f"successful no match: {selection}, {res}")
        return None
    if len(best_matches) == 1:
        log.debug(f"successful match: {selection}, {best_matches}")
        return best_matches[0][0]

    log.debug(f"{selection} has multiple best matches {best_matches}")

    return _prompt_for_match(selection, potential_selections)


def match_or_register_events(
    lock, sb: str, sb_get_events: Callable[[], list[Event]]
):
    log.info(f"match_or_register_events for {sb}")
    for event in sb_get_events():
        db.match_or_register_event(lock, sb, event, _maybe_match_event)


def _maybe_match_market(
    market: Market, potential_markets: list[Market]
) -> Market | None:
    # Compare everything except player which needs fuzzy comparison.
    equals = (
        lambda a, b: a.name == b.name
        and a.kind == b.kind
        and a.period == b.period
        and a.line == b.line
    )

    potential_equal_markets = [
        m for m in potential_markets if equals(market, m)
    ]

    # if not a player market
    if market.player is None:
        equal_markets = [m for m in potential_equal_markets if m.player is None]
        if len(equal_markets) > 1:
            log.error(
                f"There should not be more than one equal markets {market},"
                f" {potential_markets}"
            )
        return equal_markets[0] if len(equal_markets) == 1 else None

    best_matches = process.extractBests(
        market,
        potential_equal_markets,
        lambda e: e.player,
        fuzz.WRatio,
        score_cutoff=79,
    )

    if len(best_matches) > 1:
        return _prompt_for_match(market, best_matches)
    if len(best_matches) == 1:
        return best_matches[0][0]
    return None


def match_or_register_markets(
    lock, sb: str, sb_get_markets: Callable[[str], list[Market]]
):
    log.info(f"match_or_register_markets for {sb}")
    sb_events = db.get_sb_events(lock, sb)
    for unified_event_id, url in sb_events:
        markets = sb_get_markets(url)
        for market in markets:
            unified_market_id = db.match_or_register_market(
                lock,
                sb,
                unified_event_id,
                market,
                _maybe_match_market,
            )
            for selection in market.selection:
                db.update_or_register_event_selection(
                    lock,
                    sb,
                    unified_market_id,
                    selection,
                    _maybe_match_selection,
                )
