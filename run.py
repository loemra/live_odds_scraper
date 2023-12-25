import asyncio
import sys

from packages.util.setup_logging import setup_root_logging

logger = setup_root_logging()


def betmgm_events():
    from packages.sbs.betmgm.get_events import yield_events

    asyncio.run(yield_events())


def run():
    if len(sys.argv) > 1:
        eval(sys.argv[1])()
    else:
        print("Must provide argument to run.")


if __name__ == "__main__":
    run()
