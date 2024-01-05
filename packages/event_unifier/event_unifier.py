import asyncio
from datetime import timedelta

from pymongo.errors import PyMongoError
from tenacity import retry, stop_after_attempt, wait_exponential

from packages.util.setup_logging import setup_logging
from packages.util.spawn import spawn


class EventUnifier:
    def __init__(self, client, db, match, logger=setup_logging(__name__)):
        self._client = client
        self._db = db
        self._match = match
        self._logger = logger

    async def run(self):
        # brief period between when reading ununified events and before listening
        # to updates where an event can sneak through without being processed
        # with the solution below, if an event is added after beginning to listen
        # and before getting ununified events it will be handled twice, which is
        # better than none

        gen = self._watch_updates()

        # start listening
        await anext(gen)
        # get ununified events
        await self._handle_existing_ununified_events()
        # continue listening
        await anext(gen)

    async def _handle_existing_ununified_events(self):
        cur = self._db.sb_events.find({"unified_id": {"$exists": False}})

        async for sb_event in cur:
            spawn(self._handle_event(sb_event))

    async def _watch_updates(self, resume_token=None):
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
                async with self._db.sb_events.watch(
                    pipeline, resume_after=resume_token
                ) as stream:
                    self._logger.info("listening to updates...")
                    if not yielded:
                        yield
                        yielded = True
                    async for update in stream:
                        resume_token = stream.resume_token
                        sb_event = update["fullDocument"]
                        spawn(self._handle_event(sb_event))
            except PyMongoError as e:
                self._logger.warning(
                    f"Error with the stream, retrying now... {e}"
                )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=20))
    async def _handle_event(self, sb_event):
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                unified_event = await self.match_existing_unified_events(
                    session, sb_event
                )

                unified_event_id = (
                    unified_event["_id"]
                    if unified_event
                    else await self._create_unified_event(session, sb_event)
                )

                await self.link_sb_to_unified_event(
                    session, sb_event["_id"], unified_event_id
                )

                async with asyncio.TaskGroup() as tg:
                    for sb_market in sb_event["markets"]:
                        tg.create_task(
                            self._handle_market(
                                session,
                                sb_event["sb"],
                                sb_market,
                                unified_event_id,
                            )
                        )

    async def match_existing_unified_events(self, session, sb_event):
        # try to match sb_event to an existing unififed event.
        self._logger.info(f"handling {sb_event['id']}")

        cur = self._db.unified_events.find(
            {
                "league": sb_event["league"],
                "date": {
                    "$gte": sb_event["date"] - timedelta(hours=2),
                    "$lte": sb_event["date"] + timedelta(hours=2),
                },
            },
            session=session,
        )

        potential_unified_events = [e async for e in cur]
        return await self._match(
            sb_event, potential_unified_events, processor=lambda x: x["name"]
        )

    async def _create_unified_event(self, session, sb_event):
        unified_event = {k: sb_event[k] for k in ["name", "league", "date"]}
        unified_event["market_ids"] = []
        res = await self._db.unified_events.insert_one(
            unified_event, session=session
        )
        self._logger.info(f"created unified event {res.inserted_id}")
        return res.inserted_id

    async def link_sb_to_unified_event(
        self, session, sb_event_id, unified_event_id
    ):
        await self._db.sb_events.update_one(
            {"_id": sb_event_id},
            {"$set": {"unified_id": unified_event_id}},
            session=session,
        )
        self._logger.info(f"linked {sb_event_id} and {unified_event_id}")

    async def _handle_market(self, session, sb, sb_market, unified_event_id):
        market_search = {
            k: v
            for k, v in sb_market.items()
            if k not in ["_id", "selections"]
        }
        market_search["event_id"] = unified_event_id
        market_odds = await self._db.market_odds.find_one(
            market_search, session=session
        )

        if market_odds is None:
            market_odds_id = await self._create_market_odds(
                session, sb, sb_market, unified_event_id
            )
            await self._link_market_odds_to_unified_event(
                session, market_odds_id, unified_event_id
            )
            return

        async with asyncio.TaskGroup() as tg:
            for sb_selection in sb_market["selections"]:
                tg.create_task(
                    self._handle_selection(
                        session, sb, sb_selection, market_odds
                    )
                )

    async def _create_market_odds(
        self, session, sb, sb_market, unified_event_id
    ):
        market_odds = sb_market.copy()
        market_odds["event_id"] = unified_event_id
        for selection in market_odds["selections"]:
            selection["odds"] = [
                {"id": selection["id"], "sb": sb, "odds": selection["odds"]}
            ]
            selection.pop("id")

        res = await self._db.market_odds.insert_one(
            market_odds, session=session
        )
        self._logger.info(f"created market odds at {res.inserted_id}")
        return res.inserted_id

    async def _link_market_odds_to_unified_event(
        self, session, market_odds_id, unified_event_id
    ):
        res = await self._db.unified_events.update_one(
            {"_id": unified_event_id},
            {"$push": {"market_ids": market_odds_id}},
            session=session,
        )
        self._logger.info(f"update this log message {res}")

    async def _handle_selection(self, session, sb, sb_selection, market_odds):
        if await self._db.market_odds.count_documents(
            {
                "_id": market_odds["_id"],
                "selections.odds.id": sb_selection["id"],
                "selections.odds.sb": sb,
            },
            session=session,
        ):
            self._logger.warning(
                f"trying to add sb_selection {sb_selection['id']} to"
                " market_odds where it already exists"
                f"\n{sb}\n{sb_selection}\n{market_odds}"
            )
            return

        if not self._match_selections(sb_selection, market_odds):
            self._logger.warning(
                f"unable to match sb_selection {sb_selection['id']} with any"
                " selections in"
                f" market_odds\n{sb}\n{sb_selection}\n{market_odds}"
            )
            raise Exception()

        await self._append_selection_odds_to_market_odds(
            session, sb, sb_selection, market_odds["_id"]
        )

    async def _match_selections(self, sb_selection, market_odds):
        return await self._match(
            sb_selection,
            market_odds["selections"],
            processor=lambda x: x["name"],
        )

    async def _append_selection_odds_to_market_odds(
        self, session, sb, sb_selection, market_odds_id
    ):
        odds = sb_selection.copy()
        odds.pop("name")
        odds["sb"] = sb

        await self._db.market_odds.update_one(
            {"_id": market_odds_id},
            {"$push": {"selections.$[selection].odds": odds}},
            array_filters=[{"selection.name": sb_selection["name"]}],
            session=session,
        )
