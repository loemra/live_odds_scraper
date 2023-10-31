import json

from packages.core.Aggregator import Aggregator
from packages.db.DB import DB
from packages.name_matcher.MockMatcher import MockMatcher
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.betmgm.Betmgm import Betmgm
from packages.sbs.fanduel.Fanduel import Fanduel
from packages.sbs.MockSB import MockSB

with open("secrets.json", "r") as f:
    secrets = json.load(f)

db = DB(secrets["db-name"])

Aggregator(
    [Betmgm(), Fanduel()],
    db,
    NameMatcher(secrets["umgpt-session-id"], secrets["umgpt-conversation"], db),
)
