import logging
import multiprocessing
import timeit
from multiprocessing import Process

import events_updater
from sportsbooks.bovada import bovada
from sportsbooks.fox_bets import fox_bets


def _setup_logger():
    logging.basicConfig(
        filename="logs/root.log",
        level=logging.INFO,
        force=True,
        format="%(asctime)s - %(levelname)s @ %(lineno)s == %(message)s",
    )
    return logging.getLogger()


_logger = _setup_logger()

db_lock = multiprocessing.Lock()


def _handle_sb(lock, sb: str, get_events, get_markets):
    time = timeit.timeit(
        lambda: events_updater.match_or_register_events(lock, sb, get_events),
        number=1,
    )
    _logger.info(f"finished events {sb} in {time} seconds")

    time = timeit.timeit(
        lambda: events_updater.match_or_register_markets(lock, sb, get_markets),
        number=1,
    )
    _logger.info(f"finished odds {sb} in {time} seconds")


def run():
    args = [
        (db_lock, "fox_bets", fox_bets.get_events, fox_bets.get_markets),
        (db_lock, "bovada", bovada.get_events, bovada.get_markets),
    ]
    proc = []
    for arg in args:
        p = Process(target=_handle_sb, args=arg)
        p.start()
        proc.append(p)

    for p in proc:
        p.join()


if __name__ == "__main__":
    run()
