import asyncio
from typing import Awaitable, Callable, Dict, Iterable, Optional, Tuple, Union

import websockets

from packages.data.OddsUpdate import OddsUpdate
from packages.util.CustomErrors import PingReceived, PongReceived
from packages.util.logs import setup_logging
from packages.util.spawner import spawn


class WebsocketsApp:
    def __init__(
        self,
        connection: Callable,
        handle_data: Callable[
            [Union[str, bytes]], Iterable[Tuple[OddsUpdate, str]]
        ],
        initial_registration: Optional[
            Callable[[websockets.WebSocketClientProtocol], Awaitable[None]]
        ] = None,
        ping: Optional[
            Callable[[websockets.WebSocketClientProtocol], Awaitable[None]]
        ] = None,
        pong: Optional[
            Callable[[websockets.WebSocketClientProtocol], Awaitable[None]]
        ] = None,
        logger=setup_logging(__name__),
    ):
        self.logger = logger
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self.producer_buffer = asyncio.Queue()

        self.connection = connection
        self.handle_data = handle_data
        self.initial_registration = initial_registration
        self.ping = ping
        self.pong = pong

        self.running = False

    async def subscribe(self, payload):
        if not self.running:
            self.running = True
            self.logger.debug("subscribing...")
            spawn(self._runner())

        q = asyncio.Queue()
        self._subscribers[payload] = q
        await self.producer_buffer.put(payload)

        while (res := await q.get()) is not None:
            yield res

    async def _runner(self):
        async for ws in self.connection():
            try:
                self.logger.debug("initial registation?")
                if self.initial_registration is not None:
                    self.logger.debug("attempting registration")
                    await self.initial_registration(ws)
                await self._handler(ws)
            except websockets.ConnectionClosed:
                self.logger.debug("connection closed.")
                continue

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

            spawn(ws.send(payload))

    async def _consumer(self, ws):
        self.logger.debug("consumer consuming...")
        while True:
            data = await ws.recv()
            try:
                for update, sub in self.handle_data(data):
                    spawn(self._subscribers[sub].put(update))
            except PongReceived:
                self.logger.debug("pong received...")
                if self.ping is not None:
                    spawn(self.ping(ws))
            except PingReceived:
                self.logger.debug("ping received...")
                if self.pong is not None:
                    spawn(self.pong(ws))
