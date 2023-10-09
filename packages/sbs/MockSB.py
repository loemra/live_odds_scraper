import time
from datetime import datetime
from functools import partial

from ..data.Event import Event
from ..data.Sport import Sport


class MockSB:
    def __init__(self):
        self.name = "Mock"

    def yieldEvents(self):
        for i in range(10):
            time.sleep(1)
            yield (
                Event(i + 1, f"Event {i+1}", datetime.now(), Sport.SOCCER),
                partial(self.yieldOdds, f"Event {i+1}"),
            )

    def yieldOdds(self, eventID):
        for i in range(10):
            time.sleep(1)
            yield f"Odds {i} for {eventID} from {self.name}"
