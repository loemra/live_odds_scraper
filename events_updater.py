import logging
from typing import Callable

from thefuzz import fuzz, process

from database import db
from datastructures.event import Event
from datastructures.selection import Selection


def _setup_logger():
    logging.basicConfig(
        filename="logs/root.log", level=logging.DEBUG, force=True
    )
    logger = logging.getLogger("events_updater")
    logger.propagate = False
    fh = logging.FileHandler("logs/events_updater.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s @ %(lineno)s == %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


_logger = _setup_logger()


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
        _logger.debug(f"successful no match: {event}, {res}")
        return None
    if len(best_matches) == 1:
        _logger.debug(f"successful match: {event}, {best_matches}")
        return best_matches[0][0]

    _logger.debug(f"{event} has multiple best matches {best_matches}")

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
        score_cutoff=79,
    )

    if not best_matches:
        res = process.extract(
            selection,
            potential_selections,
            lambda e: e.name,
            custom_scorer,
        )
        _logger.debug(f"successful no match: {selection}, {res}")
        return None
    if len(best_matches) == 1:
        _logger.debug(f"successful match: {selection}, {best_matches}")
        return best_matches[0][0]

    _logger.debug(f"{selection} has multiple best matches {best_matches}")

    return _prompt_for_match(selection, potential_selections)


def match_or_register_events(
    lock, sb: str, sb_get_events: Callable[[], list[Event]]
):
    for event in sb_get_events():
        db.match_or_register_event(lock, sb, event, _maybe_match_event)


def update_or_register_event_selections(
    lock,
    sb: str,
    sb_get_odds: Callable[[str], list[Selection]],
):
    sb_events = db.get_sb_events(lock, sb)
    for unified_event_id, url in sb_events:
        selections = sb_get_odds(url)
        for selection in selections:
            db.update_or_register_event_selections(
                lock, sb, unified_event_id, selection, _maybe_match_selection
            )
