import json
import logging

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
from packages.util.logs import setup_root_logging

setup_root_logging()

sw_handler = logging.FileHandler("logs/seleniumwire.log")
sw_handler.setFormatter(
    logging.Formatter("%(name)s - %(levelname)s - %(message)s")
)
sw_logger = logging.getLogger("seleniumwire")
sw_logger.setLevel(logging.INFO)
sw_logger.addHandler(sw_handler)

with open("secrets.json", "r") as f:
    secrets = json.load(f)

db = DB(secrets["db-name"])

Aggregator(
    [Betmgm(), Fanduel(), Betrivers()],
    db,
    FuzzMatcher(
        db,
        fallback_matcher=NameMatcher(
            secrets["umgpt-session-id"], secrets["umgpt-conversation"], MockDB()
        ),
    ),
    # NameMatcher(secrets["umgpt-session-id"], secrets["umgpt-conversation"], db),
)
