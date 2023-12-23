import json
import sys
from queue import Queue
from threading import Thread

from packages.core.EventAggregator import EventAggregator
from packages.core.OddsAggregator import OddsAggregator
from packages.db.DB import DB
from packages.db.MockDB import MockDB
from packages.gui.gui import GUI
from packages.name_matcher.FuzzMatcher import FuzzMatcher
from packages.name_matcher.MockMatcher import MockMatcher
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.betmgm.Betmgm import Betmgm
from packages.sbs.betrivers.Betrivers import Betrivers
from packages.sbs.draftkings.DraftKings import DraftKings
from packages.sbs.fanduel.Fanduel import Fanduel
from packages.sbs.MockSB import MockSB
from packages.sbs.pointsbet.PointsBet import PointsBet
from packages.util.logs import setup_root_logging, setup_seleniumwire_logging

setup_root_logging()
setup_seleniumwire_logging()

with open("secrets.json", "r") as f:
    secrets = json.load(f)

db = DB(secrets["db-name"])

gui = GUI(db)
Thread(target=gui.run(), daemon=True).start()

if len(sys.argv) == 1:
    sbs = [Betmgm(), Fanduel(), Betrivers(), DraftKings(), PointsBet()]
else:
    sbs = [eval(sb)() for sb in sys.argv[1:]]

queues = []

for sb in sbs:
    payload_queue = Queue()
    queues.append(payload_queue)

    EventAggregator(
        sb,
        db,
        FuzzMatcher(
            db,
            fallback_matcher=NameMatcher(
                secrets["umgpt-session-id"],
                secrets["umgpt-conversation"],
                MockDB(),
            ),
        ),
        payload_queue,
    )

    OddsAggregator(sb, db, payload_queue)
