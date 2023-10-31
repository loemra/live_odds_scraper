import queue
from functools import partial
from threading import Thread

import requests

from packages.sbs.betmgm.handlers.NFL import NFL
from packages.util.UserAgents import get_random_user_agent


class Betmgm:
    def __init__(self):
        self.name = "betmgm"
        self.s = Betmgm._establish_session()
        self.handlers = [NFL(self.s)]

    def yield_events(self):
        buffer = queue.Queue()
        for handler in self.handlers:
            Thread(
                target=Betmgm._event_producer, args=(buffer, handler)
            ).start()

        while True:
            event = buffer.get()
            yield (
                event,
                partial(self.yield_odd_updates, event.id),
            )

    @staticmethod
    def _event_producer(buffer, handler):
        for event in handler.yield_events():
            buffer.put(event)

    def yield_odd_updates(self, eventID):
        pass

    @staticmethod
    def _establish_session():
        s = requests.Session()
        s.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "sports.mi.betmgm.com",
            "Origin": "null",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": get_random_user_agent(),
        }
        s.get("https://sports.mi.betmgm.com/")

        return s
