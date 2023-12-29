from datetime import timedelta
from functools import partial

from bson.objectid import ObjectId
from pymongo.errors import PyMongoError

from packages.event_unifier.name_matcher import FuzzMatcher, GPTMatcher
from packages.util.setup_logging import setup_logging
from packages.util.spawn import spawn

_logger = setup_logging(__name__, True)


async def run(db):
    # brief period between when reading ununified events and before listening
    # to updates where an event can sneak through without being processed
    # with the solution below, if an event is added after beginning to listen
    # and before getting ununified events it will be handled twice, which is
    # better than none

    gen = _watch_updates(db)

    # start listening
    await anext(gen)
    # get ununified events
    await _handle_existing_ununified_events(db)
    # continue listening
    await anext(gen)


async def _handle_existing_ununified_events(db):
    cur = db.sb_events.find({"unified_id": {"$exists": False}})

    async for event in cur:
        spawn(_handle_event(db, event))


async def _watch_updates(db, resume_token=None):
    pipeline = [
        {
            "$match": {
                "operationType": {"$in": ["insert", "replace"]},
                "fullDocument.unified_id": {"$exists": False},
            }
        }
    ]
    yielded = False

    while True:
        try:
            async with db.sb_events.watch(
                pipeline, resume_after=resume_token
            ) as stream:
                _logger.info("listening to updates...")
                if not yielded:
                    yield
                    yielded = True
                async for update in stream:
                    resume_token = stream.resume_token
                    event = update["fullDocument"]
                    spawn(_handle_event(db, event))
        except PyMongoError as e:
            _logger.warning(f"Error with the stream, retrying now... {e}")


async def _handle_event(db, event):
    _logger.info(f"handling {event['id']}")

    cur = db.unified_events.find({
        "league": event["league"],
        "date": {
            "$gte": event["date"] - timedelta(hours=2),
            "$lte": event["date"] + timedelta(hours=2),
        },
    })

    def processor(e):
        return e["name"]

    potential_unified_events = [e async for e in cur]
    if (
        unified_event := await FuzzMatcher.match(
            event,
            potential_unified_events,
            partial(
                GPTMatcher.match,
                processor=processor,
            ),
            processor=processor,
        )
    ) is None:
        unified_event = await _create_unified_event(db, event)

    await _link_to_unified_event(db, event, unified_event)


async def _create_unified_event(db, event):
    unified_event = event.copy()
    sb = unified_event["sb"]
    unified_event.pop("_id")
    unified_event.pop("id")
    unified_event.pop("sb")
    unified_event.pop("payload")
    for market in unified_event["markets"]:
        market["_id"] = ObjectId()
        spawn(_create_market_odds(db, sb, market.copy()))
        market.pop("selections")

    res = await db.unified_events.insert_one(unified_event)
    unified_event["_id"] = res.inserted_id
    _logger.info(f"created unified event {unified_event['_id']}")
    return unified_event


async def _create_market_odds(db, sb, market):
    market_odds = market.copy()
    market_odds.pop("name")
    market_odds.pop("kind")

    for selection in market_odds["selections"]:
        id = selection["id"]
        odds = selection["odds"]
        selection.pop("id")
        selection["odds"] = [{"id": id, "sb": sb, "odds": odds}]

    res = await db.market_odds.insert_one(market_odds)
    _logger.info(f"created market odds at {res.inserted_id}")


async def _link_to_unified_event(db, event, unified_event):
    await db.sb_events.update_one(
        {"_id": event["_id"]},
        {"$set": {"unified_id": unified_event["_id"]}},
    )
    _logger.info(f"linked {event['id']} to {unified_event['_id']}")
