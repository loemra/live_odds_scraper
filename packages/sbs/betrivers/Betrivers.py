import queue
from functools import partial
from threading import Thread

from packages.sbs.betrivers.handlers.NFL import NFL


class Betrivers:
    def __init__(self):
        self.name = "betrivers"
        self.handlers = [NFL()]

    def yield_events(self):
        buffer = queue.Queue()
        for handler in self.handlers:
            Thread(
                target=Betrivers._event_producer, args=(buffer, handler)
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