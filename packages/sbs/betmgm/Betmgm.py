import json
import queue
from datetime import datetime
from functools import partial
from threading import Thread

from websockets.sync.client import connect

from packages.data.OddsUpdate import OddsUpdate
from packages.sbs.betmgm.scrapers.NFL import NFL
from packages.util.CustomErrors import PingReceived
from packages.util.logs import setup_logging
from packages.util.WebsocketsApp import WebsocketsApp


class Betmgm:
    def __init__(self):
        self.logger = setup_logging(__name__, True)
        self.name = "betmgm"
        self.handlers = [NFL()]

        self.wsapp = WebsocketsApp(
            connection=partial(
                connect,
                "wss://cds-push.mi.betmgm.com/ws-1-0?"
                "lang=en-us&country=US&x-bwin-accessId="
                "NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&"
                "appUpdates=false",
            ),
            handle_data=self._handle_data,
            initial_registration=self._initial_registration,
            pong=self._pong,
            logger=self.logger,
        )

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

    async def yield_odd_updates(self, payload: str):
        full_payload = (
            b'{"arguments":[{"topics":["{'
            + payload.encode()
            + b'}"]}],"invocationId":"0","target":"Subscribe","type":1}\x1e'
        )

        async for res in self.wsapp.subscribe(full_payload):
            yield res

    async def _initial_registration(self, ws):
        self.logger.debug("sending registration...")
        await ws.send(b'{"protocol":"json","version":1}\x1e')
        self.logger.debug(await ws.recv())
        self.logger.debug(await ws.recv())

    async def _pong(self, ws):
        self.logger.debug("sending pong...")
        await ws.send(b'{"type":6}')
        self.logger.debug("pong sent")

    def _handle_data(self, data):
        self.logger.debug(f"handling data... {data}")
        if isinstance(data, str):
            data = data.encode()
        for r in data.split(b"\x1e"):
            try:
                j = json.loads(r)
            except json.JSONDecodeError:
                continue

            if j["type"] == 6:
                raise PingReceived()
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
