from threading import Thread

from packages.data.MarketName import MarketName
from packages.util.logs import setup_logging


class EventAggregator:
    def __init__(self, sb, db, name_matcher, payload_queue):
        self.sb = sb
        self.db = db
        self.name_matcher = name_matcher
        self.payload_queue = payload_queue
        self.logger = setup_logging(__name__)

        Thread(target=self._handle_sb_event).start()

    def _handle_sb_event(self):
        self.logger.debug("Event Aggregator running...")
        for event in self.sb.yield_events():
            # filter just the money lines for now
            event.markets = [
                m for m in event.markets if m.name == MarketName.MONEY_LINE
            ]
            self.logger.debug(f"Sending event to db {event}")
            self.db.match_or_make_event(event, self.sb.name, self.name_matcher)

            self.logger.debug(
                f"Sending payload to queue {event.odds_retrieval_payload}"
            )
            self.payload_queue.put(event.odds_retrieval_payload)
