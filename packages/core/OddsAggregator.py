import asyncio
from threading import Thread
from packages.util.logs import setup_logging

from packages.util.spawner import spawn


class OddsAggregator:
    def __init__(self, sb, db, payload_queue):
        self.sb = sb
        self.db = db
        self.payload_queue = payload_queue
        self.logger = setup_logging(__name__)

        # Thread(target=self._receiver).start()
        asyncio.run(self._receiver())

    async def _receiver(self):
        self.logger.debug("Receiving payloads...")
        loop = asyncio.get_running_loop()
        while True:
            payload = await loop.run_in_executor(None, self.payload_queue.get)
            self.logger.debug(f"Got payload {payload}.")
            spawn(self._handle_odd_updates(payload))

    async def _handle_odd_updates(self, payload):
        self.logger.debug(f"Handling odds updates for {payload}")
        async for update in self.sb.yield_odd_updates(payload):
            self.logger.debug(f"Sending odds update {update} to db...")
            self.db.update_odds(update)
