import asyncio
import json
from datetime import datetime

import websockets

from packages.data.OddsUpdate import OddsUpdate
from packages.util.CustomErrors import PingReceived
from packages.util.logs import setup_logging
from packages.util.spawner import spawn


# NOT THREAD SAFE.
class Tmp:
    def __init__(self):
        self.name = "TMP"
        self.ws_link = "wss://cds-push.mi.betmgm.com/ws-1-0?lang=en-us&country=US&x-bwin-accessId=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&appUpdates=false"
        self.logger = setup_logging(__name__, True)

        self.subscribers = {}
        self.producer_buffer = asyncio.Queue()

        spawn(self._runner())

    async def yield_odds_update(self, payload):
        queue = asyncio.Queue()
        self.subscribers[payload] = queue
        await self.producer_buffer.put(payload)

        while True:
            yield await queue.get()

    async def _runner(self):
        async for ws in websockets.connect(self.ws_link):
            try:
                await self._initial_registration(ws)
                await self._handler(ws)
            except websockets.ConnectionClosed:
                self.logger.debug("connection closed.")
                continue

    async def _initial_registration(self, ws):
        self.logger.debug("sending registration...")
        await ws.send(b'{"protocol":"json","version":1}\x1e')
        self.logger.debug(await ws.recv())
        self.logger.debug(await ws.recv())

    async def _pong(self, ws):
        self.logger.debug("sending pong...")
        await ws.send(b'{"type":6}')
        self.logger.debug("pong sent")

    async def _handler(self, ws):
        await asyncio.gather(
            self._consumer(ws),
            self._producer(ws),
        )

    async def _producer(self, ws):
        self.logger.debug("producer producing...")
        while True:
            payload = await self.producer_buffer.get()
            self.logger.debug(f"producer received payload {payload}")

            spawn(
                ws.send(
                    b'{"arguments":[{"topics":["{'
                    + payload.encode()
                    + b'}"]}],"invocationId":"0","target":"Subscribe","type":1}\x1e'
                )
            )

    async def _consumer(self, ws):
        self.logger.debug("consumer consuming...")
        while True:
            data = await ws.recv()
            try:
                for update, sub in self._handle_data(data):
                    spawn(self.subscribers[sub].put(update))
            except PingReceived:
                self.logger.debug("ping received...")
                spawn(self._pong(ws))

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
