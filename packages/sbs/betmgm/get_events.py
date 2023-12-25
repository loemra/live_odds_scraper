import asyncio

from packages.sbs.betmgm.scrapers.nba import NBA
from packages.sbs.betmgm.scrapers.nfl import NFL
from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__, True)


async def yield_events():
    scrapers = [NFL(_logger), NBA(_logger)]
    async with asyncio.TaskGroup() as tg:
        for scraper in scrapers:
            tg.create_task(_process_scraper(scraper, tg))


async def _process_scraper(scraper, tg):
    async for event in scraper.yield_events():

        async def _db_to_stream(e):
            await _write_to_db(e)

        tg.create_task(_db_to_stream(event))


async def _write_to_db(data):
    pass
