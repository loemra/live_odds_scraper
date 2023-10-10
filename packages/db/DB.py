import sqlite3
from threading import Lock
from typing import List

from packages.data.EventRegistration import EventRegistration
from packages.event_matcher.EventMatcher import EventMatcher
from packages.sbs.MockSB import Event


class DB:
    def __init__(self, name):
        self.con = sqlite3.connect(name)
        self.lock = Lock()

    def matchOrRegisterEvent(
        self, sb_event, event_matcher: EventMatcher
    ) -> EventRegistration:
        unified_event = event_matcher.match(
            sb_event, self._get_relevant_events(sb_event)
        )

        # no match.
        if unified_event is None:
            unified_event = self._make_unified_event(sb_event)

        return self._register_sb_event(sb_event, unified_event)

    def _get_relevant_events(self, event) -> List[Event]:
        return []

    def _make_unified_event(self, sb_event) -> Event:
        return sb_event

    def _register_sb_event(self, sb_event, unified_event) -> EventRegistration:
        return EventRegistration()

    def updateOdds(self):
        pass
