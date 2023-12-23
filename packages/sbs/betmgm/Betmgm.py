import json
import queue
from datetime import datetime
from functools import partial
from threading import Thread

from websockets import connect

from packages.data.OddsUpdate import OddsUpdate
from packages.sbs.betmgm.scrapers.NBA import NBA
from packages.sbs.betmgm.scrapers.NFL import NFL
from packages.util.CustomErrors import PingReceived
from packages.util.logs import setup_logging
from packages.util.WebsocketsApp import WebsocketsApp


class Betmgm:
    def __init__(self):
        self.logger = setup_logging(__name__)
        self.name = "betmgm"
        self.scrapers = [NFL(self.logger), NBA(self.logger)]

        self.invocationID = -1
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
        for scraper in self.scrapers:
            Thread(target=self._event_producer, args=(buffer, scraper)).start()

        scrapers = len(self.scrapers)
        while True:
            event = buffer.get()
            if event is None:
                scrapers -= 1
                if scrapers == 0:
                    break
                continue
            yield event

    def _event_producer(self, buffer, handler):
        for event in handler.yield_events():
            buffer.put(event)
        buffer.put(None)

    def _encode_payload(self, payload):
        self.invocationID += 1
        return (
            b'{"arguments":[{"topics":["'
            + payload.encode()
            + b'"]}],"invocationId":"'
            + str(self.invocationID).encode()
            + b'","target":"Subscribe","type":1}\x1e'
        )

    async def yield_odd_updates(self, payload: str):
        self.logger.debug(f"Subscribing to payload {payload}")
        async for res in self.wsapp.subscribe(
            payload, self._encode_payload(payload)
        ):
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
        if isinstance(data, str):
            data = data.encode()
        for r in data.split(b"\x1e"):
            try:
                j = json.loads(r)
            except json.JSONDecodeError:
                continue

            self.logger.debug(f"received {j['type']}\n{data}")

            if j["type"] == 6:
                raise PingReceived()
            if j["type"] != 1:
                continue
            for argument in j["arguments"]:
                if not isinstance(argument, dict):
                    continue
                match argument["messageType"]:
                    case "GameUpdate":
                        for result in argument["payload"]["game"]["results"]:
                            yield (
                                OddsUpdate(
                                    str(result["id"]),
                                    self.name,
                                    result["odds"],
                                    datetime.fromisoformat(argument["timestamp"]),
                                ),
                                argument["topic"],
                            )
                    case "MainToLiveUpdate":
                        pass
                    case _:
                        continue

