import asyncio
import json
import queue
import threading
from datetime import datetime
from json import JSONDecodeError
from threading import Thread

import requests
from websockets import ConnectionClosed
from websockets.sync.client import connect

from packages.data.OddsUpdate import OddsUpdate
from packages.sbs.betmgm.scrapers.NFL import NFL
from packages.util.logs import setup_logging
from packages.util.UserAgents import get_random_user_agent


class Betmgm:
    def __init__(self):
        self.logger = setup_logging(__name__, True)
        self.name = "betmgm"
        self.s = self._establish_session()
        self.handlers = [NFL(self.s)]

        self.lock = threading.Lock()
        self.subscribers = {}

        self.connection = self._establish_websocket()
        self.MAX_RETRIES = 5
        self.retries = 0
        Thread(target=self._odds_receiver, daemon=True).start()

    def yield_events(self):
        buffer = queue.Queue()
        for handler in self.handlers:
            Thread(target=self._event_producer, args=(buffer, handler)).start()

        while True:
            event = buffer.get()
            if event is None:
                break
            yield (event, None)

    def _event_producer(self, buffer, handler):
        for event in handler.yield_events():
            buffer.put(event)
        buffer.put(None)

    def _establish_session(self):
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

    def _establish_websocket(self):
        self.logger.debug("establishing websocket...")
        connection = connect(
            "wss://cds-push.mi.betmgm.com/ws-1-0?lang=en-us&country=US&x-bwin-accessId=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&appUpdates=false"
        )
        with connection as ws:
            ws.send(b'{"protocol":"json","version":1}\x1e')
            self.logger.debug(ws.recv())
            self.logger.debug(ws.recv())

        return connection

    def _odds_receiver(self):
        try:
            for data in self.connection.recv():
                with self.lock:
                    self.retries = 0
                for update, sub in self._handle_data(data):
                    with self.lock:
                        self.subscribers[sub].put(update)
        except ConnectionClosed as _:
            # there could be an additional error here that gets called if the underlying connection changes while receiving.
            # for example if there is an error sending and the connection is reconnected.
            pass

    # odds_payload = ["fixture][*]["context"]
    def yield_odd_updates(self, odds_payload: str):
        buffer = queue.Queue()
        self._subscribe(odds_payload, buffer)

        for update in iter(buffer.get, None):
            yield update

    def _handle_data(self, data):
        self.logger.debug(f"received {data}")
        for r in data.split(b"\x1e"):
            try:
                j = json.loads(r)
            except JSONDecodeError as _:
                continue

            if j["type"] != 1:
                continue
            for argument in j["arguments"]:
                if (
                    not isinstance(argument, dict)
                    or argument["messageType"] != "GameUpdate"
                ):
                    continue
                for payload in argument["payload"]:
                    for game in payload["game"]:
                        for result in game["results"]:
                            yield (
                                OddsUpdate(
                                    str(result["id"]),
                                    self.name,
                                    result["odds"],
                                    datetime.fromisoformat(
                                        argument["timestamp"]
                                    ),
                                ),
                                argument["topic"],
                            )

    def _subscribe(self, odds_payload: str, buffer):
        self.logger.debug(f"sending subscribe payload...")
        with self.lock:
            self.subscribers[odds_payload] = buffer
        try:
            self.connection.send(
                b'{"arguments":[{"topics":["{'
                + odds_payload.encode()
                + b'}"]}],"invocationId":"0","target":"Subscribe","type":1}\x1e'
            )
            with self.lock:
                self.retries = 0
        except ConnectionClosed as _:
            with self.lock:
                if self.retries > self.MAX_RETRIES:
                    raise
                self.logger.debug(
                    "connection closed... retrying"
                    f" {self.retries}/{self.MAX_RETRIES}"
                )
                self.connection = self._establish_websocket()
                self.retries += 1
