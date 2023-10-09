from threading import Lock, Thread


class Aggregator:
    def __init__(self, sbs, db, translater, event_matcher):
        self.db = db
        self.translater = translater
        self.event_matcher = event_matcher
        self.lock = Lock()

        for sb in sbs:
            Thread(target=self.handleSBEvent, args=(sb,)).start()

    def handleSBEvent(self, sb):
        for event, yieldOdds in sb.yieldEvents():
            with self.lock:
                ids = self.db.matchOrRegisterEvent(event, self.event_matcher)
                self.translater.add_ids(*ids)

            Thread(target=self.handleOdds, args=(yieldOdds,)).start()

    def handleOdds(self, yieldOdds):
        for odds in yieldOdds():
            with self.lock:
                print(odds)
