import json

from packages.core.Aggregator import Aggregator
from packages.db.DB import DB
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.MockSB import MockSB

with open("secrets.json", "r") as f:
    secrets = json.load(f)

db = DB(secrets["db-name"])

Aggregator(
    [MockSB()],
    db,
    NameMatcher(secrets["umgpt-session-id"], secrets["umgpt-conversation"], db),
)
