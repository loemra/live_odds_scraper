import asyncio
import sys

import motor.motor_asyncio as motor

from packages.util.setup_logging import setup_root_logging

logger = setup_root_logging()


def _get_db():
    client = motor.AsyncIOMotorClient("mongodb://localhost:27017/")
    return client.arb


def betmgm_events():
    from packages.sbs.betmgm.handle_events import handle_events

    db = _get_db()
    asyncio.run(handle_events(db))


def event_unifier():
    from packages.event_unifier.event_unifier import run

    db = _get_db()
    asyncio.run(run(db))


def run():
    if len(sys.argv) > 1:
        eval(sys.argv[1])()
    else:
        print("Must provide argument to run.")


if __name__ == "__main__":
    run()
