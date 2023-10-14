import time
from datetime import datetime
from functools import partial

from packages.data.Event import Event
from packages.data.League import League
from packages.data.OddsUpdate import OddsUpdate
from packages.data.Sport import Sport


class MockSB:
    def __init__(self):
        self.name = "Mock"

    def yieldEvents(self):
        for i in range(10):
            time.sleep(1)
            yield (
                Event(
                    i + 1,
                    f"Event {i+1}",
                    datetime.now(),
                    Sport.SOCCER,
                    League.PREMIER,
                ),
                partial(self.yieldOddsUpdates, f"Event {i+1}"),
            )

    def yieldOddsUpdates(self, eventID):
        for i in range(10):
            time.sleep(1)
            yield OddsUpdate(i + 1, self.name, 1.7, datetime.now())
