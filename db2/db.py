import sqlite3
from typing import Callable

from datastructures.event import EventMetadata
from datastructures.market import MarketMetadata
from datastructures.selection import SelectionMetadata
from datastructures.update import Update

conn = sqlite3.connect(":memory:")


def clear_db():
    pass


# EVENTS


def get_events() -> list[EventMetadata]:
    pass


def match_or_register_event(
    maybe_match: Callable[[list[EventMetadata]], EventMetadata | None],
    unify: Callable[[], EventMetadata],
) -> EventMetadata:
    pass


# MAKRETS


def get_markets(event_id: str) -> list[MarketMetadata]:
    pass


def maybe_register_market(event_id: str, market: MarketMetadata):
    pass


# SELECTIONS


def match_or_register_selection(
    event_id: str,
    market_id: str,
    maybe_match: Callable[[list[SelectionMetadata]], SelectionMetadata | None],
    unify: Callable[[], SelectionMetadata],
) -> SelectionMetadata:
    pass


# UDPATE


def update_event_odds(update: Update):
    pass
