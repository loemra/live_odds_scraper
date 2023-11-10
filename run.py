import json
import sys

from packages.core.Aggregator import Aggregator
from packages.db.DB import DB
from packages.db.MockDB import MockDB
from packages.name_matcher.FuzzMatcher import FuzzMatcher
from packages.name_matcher.MockMatcher import MockMatcher
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.betmgm.Betmgm import Betmgm
from packages.sbs.betrivers.Betrivers import Betrivers
from packages.sbs.fanduel.Fanduel import Fanduel
from packages.sbs.MockSB import MockSB
from packages.sbs.pointsbet.PointsBet import PointsBet
from packages.util.logs import setup_root_logging, setup_seleniumwire_logging

setup_root_logging()
setup_seleniumwire_logging()

with open("secrets.json", "r") as f:
    secrets = json.load(f)

db = DB(secrets["db-name"])

if len(sys.argv) == 1:
    sbs = [Betmgm(), Fanduel(), Betrivers(), PointsBet()]
else:
    sbs = [eval(sb)() for sb in sys.argv[1:]]


Aggregator(
    sbs,
    db,
    FuzzMatcher(
        db,
        fallback_matcher=NameMatcher(
            secrets["umgpt-session-id"], secrets["umgpt-conversation"], MockDB()
        ),
    ),
)
