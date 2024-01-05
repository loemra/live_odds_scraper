import pprint
from datetime import datetime, timedelta
from functools import partial

import motor.motor_asyncio as motor
from bson import ObjectId

from packages.event_unifier.event_unifier import EventUnifier
from packages.event_unifier.name_matcher.MockMatcher import gen, match
from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__, True)


async def _get_client_db():
    client = motor.AsyncIOMotorClient()
    await client.drop_database("test")
    return (client, client.test)


sb_event1 = {
    "_id": ObjectId(),
    "id": "15175181",
    "name": "Las Vegas Raiders at Indianapolis Colts",
    "sb": "BETMGM",
    "league": "NFL",
    "date": datetime.now(),
    "payload": "v1|en-us|15175181|v2|2:6392261|all",
    "markets": [
        {
            "name": "money_line",
            "kind": "h2h",
            "selections": [
                {"id": "-1285509377", "name": "Raiders", "odds": 2.5},
                {"id": "-1285509376", "name": "Colts", "odds": 1.55},
            ],
        }
    ],
}

sb_event2 = {
    "_id": ObjectId(),
    "id": "random",
    "name": "Raiders versus Colts",
    "sb": "FOXBETS",
    "league": "NFL",
    "date": datetime.now() + timedelta(hours=1),
    "payload": "djsflkjsdflkj",
    "markets": [
        {
            "name": "money_line",
            "kind": "h2h",
            "selections": [
                {"id": "-sb21", "name": "Raiders", "odds": 2.6},
                {"id": "-sb22", "name": "Colts", "odds": 1.45},
            ],
        }
    ],
}

sb_event3 = {
    "_id": ObjectId(),
    "id": "random",
    "name": "Raiders versus Colts",
    "sb": "ESPN",
    "league": "NFL",
    "date": datetime.now() + timedelta(hours=-1),
    "payload": "djsflkjsdflkj",
    "markets": [
        {
            "name": "spread",
            "kind": "h2h",
            "line": -3.5,
            "selections": [
                {"id": "-sb31", "name": "Raiders", "odds": 100},
                {"id": "-sb32", "name": "Colts", "odds": 22},
            ],
        }
    ],
}


async def test_handle_event():
    client, db = await _get_client_db()
    mock_matcher = partial(match, gen([None, 0, 0]))
    eu = EventUnifier(client, db, mock_matcher)

    await db.sb_events.insert_one(sb_event1)
    # should create a new unified_event
    await eu._handle_event(sb_event1)

    assert 1 == await db.sb_events.count_documents({})
    sb_event = await db.sb_events.find_one({})
    _logger.info(pprint.pformat(sb_event))
    keys = ["_id", "unified_id"]
    for key in keys:
        assert key in sb_event

    assert 1 == await db.unified_events.count_documents({})
    event = await db.unified_events.find_one({})
    _logger.info(pprint.pformat(event))
    key_compare = [
        ("_id", "unified_id"),
        ("name", "name"),
        ("league", "league"),
        ("date", "date"),
    ]
    for event_key, sb_event_key in key_compare:
        assert event[event_key] == sb_event[sb_event_key]

    assert 1 == await db.market_odds.count_documents({})
    market_odds = await db.market_odds.find_one({})
    _logger.info(pprint.pformat(market_odds))
    assert market_odds["event_id"] == event["_id"]
    assert market_odds["name"] == "money_line"
    assert market_odds["kind"] == "h2h"
    for s in market_odds["selections"]:
        assert "name" in s
        assert len(s["odds"]) == 1
        for odds in s["odds"]:
            assert odds["id"] in ["-1285509377", "-1285509376"]
            assert odds["sb"] == "BETMGM"
            assert "odds" in odds

    names = [s["name"] for s in market_odds["selections"]]
    assert "Raiders" in names and "Colts" in names

    await db.sb_events.insert_one(sb_event2)
    await eu._handle_event(sb_event2)

    await db.sb_events.insert_one(sb_event3)
    await eu._handle_event(sb_event3)

    _logger.debug(pprint.pformat([e async for e in db.sb_events.find()]))
    _logger.debug(pprint.pformat([e async for e in db.unified_events.find()]))
    _logger.debug(pprint.pformat([e async for e in db.market_odds.find()]))


async def run():
    await test_handle_event()
