from typing import List

from packages.sbs.MockSB import Event


class DB:
    def __init__(self):
        pass

    def matchOrRegisterEvent(self, event, event_matcher):
        for unified_event in self._get_relevant_events():
            event_matcher(event, unified_event)

        return ("sb_ids", "event_ids")

    def updateOdds(self):
        pass

    def _get_relevant_events(self) -> List[Event]:
        return []
