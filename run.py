import json

from packages.core.Aggregator import Aggregator
from packages.core.Translater import Translater
from packages.db.DB import DB
from packages.event_matcher.EventMatcher import EventMatcher
from packages.sbs.MockSB import MockSB

with open("secrets.json", "r") as f:
    secrets = json.load(f)

Aggregator(
    [MockSB()],
    DB(),
    Translater(),
    EventMatcher(secrets["umgpt-session-id"], secrets["umgpt-conversation"]),
)
