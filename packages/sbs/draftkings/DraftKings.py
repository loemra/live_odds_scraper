import queue
from functools import partial
from threading import Thread

from packages.sbs.draftkings.handlers.NFL import NFL


class DraftKings:
    def __init__(self):
        self.name = "draftkings"
        self.handlers = [NFL()]

    def yield_events(self):
        buffer = queue.Queue()
        for handler in self.handlers:
            Thread(
                target=DraftKings._event_producer, args=(buffer, handler)
            ).start()

        while True:
            event = buffer.get()
            if event is None:
                break
            yield (
                event,
                partial(self.yield_odd_updates, event.id),
            )

    @staticmethod
    def _event_producer(buffer, handler):
        for event in handler.yield_events():
            buffer.put(event)
        buffer.put(None)

    def yield_odd_updates(self, event_id):
        pass
