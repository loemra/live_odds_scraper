import asyncio

from packages.sbs.betmgm.scrapers.nba import NBA
from packages.sbs.betmgm.scrapers.nfl import NFL
from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__, True)
_sb = "BETMGM"


async def handle_events(db):
    scrapers = [
        NFL(_sb, setup_logging(f"{__name__}.nfl")),
        NBA(_sb, setup_logging(f"{__name__}.nba")),
    ]
    async with asyncio.TaskGroup() as tg:
        for scraper in scrapers:
            tg.create_task(_process_scraper(db, scraper, tg))


async def _process_scraper(db, scraper, tg):
    _logger.debug(f"processing scraper {scraper}")
    async for event in scraper.yield_events():
        tg.create_task(_write_to_db(db, event))


async def _write_to_db(db, event):
    _logger.debug(f"writing to db {event['id']}")

    # replace or write
    res = await db.sb_events.replace_one({"id": event["id"]}, event, True)

    _logger.info(
        f"successful event write to db at {res.upserted_id} for {event['id']}"
    )
