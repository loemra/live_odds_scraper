import asyncio

from packages.sbs.betmgm.scrapers.nba import NBA
from packages.sbs.betmgm.scrapers.nfl import NFL
from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__, True)


async def handle_events(db):
    scrapers = [
        NFL(setup_logging(f"{__name__} nfl")),
        NBA(setup_logging(f"{__name__} nba")),
    ]
    async with asyncio.TaskGroup() as tg:
        for scraper in scrapers:
            tg.create_task(_process_scraper(db, scraper, tg))


async def _process_scraper(db, scraper, tg):
    _logger.debug(f"processing scraper {scraper.league}")
    async for event in scraper.yield_events():
        tg.create_task(_write_to_db(db, event))


async def _write_to_db(db, data):
    _logger.debug(f"writing to db {data['id']}")

    # replace or write
    res = await db.sb_events.replace_one({"id": data["id"]}, data, True)

    _logger.info(
        f"successful write to db at {res.upserted_id} for {data['id']}"
    )
