from threading import Thread


class Aggregator:
    def __init__(self, sbs, db, name_matcher):
        self.db = db
        self.name_matcher = name_matcher

        for sb in sbs:
            Thread(target=self.handleSBEvent, args=(sb,)).start()

    def handleSBEvent(self, sb):
        for event, yieldOddsUpdates in sb.yield_events():
            self.db.match_or_make_event(event, sb.name, self.name_matcher)

            Thread(target=self.handleOdds, args=(yieldOddsUpdates,)).start()

    def handleOdds(self, yieldOddsUpdates):
        pass
