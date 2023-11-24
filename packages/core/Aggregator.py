from threading import Thread

from packages.data.MarketName import MarketName


class Aggregator:
    def __init__(self, sbs, db, name_matcher):
        self.db = db
        self.name_matcher = name_matcher

        for sb in sbs:
            Thread(target=self._handle_sb_event, args=(sb,)).start()

    def _handle_sb_event(self, sb):
        for event, _ in sb.yield_events():
            # filter just the money lines for now
            event.markets = [
                m for m in event.markets if m.name == MarketName.MONEY_LINE
            ]
            self.db.match_or_make_event(event, sb.name, self.name_matcher)

    def _handle_odds(self, sb):
        for odds in sb.yield_odd_updates():
            print(odds)
