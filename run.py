import logging
import sys
from multiprocessing import Lock, Process

import events_updater
import util.logger_setup as logger_setup
from sportsbooks.bovada import bovada
from sportsbooks.fox_bets import fox_bets


def _handle_sb(sb: str, get_events, get_markets, lock):
    if lock is None:
        lock = Lock()

    events_updater.match_or_register_events(lock, sb, get_events)
    events_updater.match_or_register_markets(lock, sb, get_markets)


def run_parallel():
    logging.info("running in parallel...")
    db_lock = Lock()

    args = [
        ("fox_bets", fox_bets.get_events, fox_bets.get_markets, db_lock),
        ("bovada", bovada.get_events, bovada.get_markets, db_lock),
    ]
    proc = []
    for arg in args:
        p = Process(target=_handle_sb, args=arg)
        p.start()
        proc.append(p)

    for p in proc:
        p.join()


def run_sequential():
    logging.info("running sequentially...")
    args = [
        ("fox_bets", fox_bets.get_events, fox_bets.get_markets, None),
        ("bovada", bovada.get_events, bovada.get_markets, None),
    ]

    for arg in args:
        _handle_sb(*arg)


if __name__ == "__main__":
    logger_setup.setup()
    if len(sys.argv) == 2:
        run_sequential()
    else:
        run_parallel()
