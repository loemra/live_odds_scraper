from threading import Thread
from datastructures.sportsbook import Sportsbook

from fox_bets.fox_bets import get_messages as fox_bets_messages
from fox_bets.fox_bets import make_sportsbook as fox_bets_make_sportsbook


sportsbooks = {}
workers = []


def poll_get_messages(sportsbook, get_messages):
    for msg in get_messages():
        sportsbook.update_odds(msg)


def register_sportsbook(sportsbook, get_messages):
    worker = Thread(
        target=poll_get_messages, daemon=True, args=(sportsbook, get_messages)
    )
    worker.start()
    workers.append(worker)


# REGISTER SPORTSBOOKS
register_sportsbook(fox_bets_make_sportsbook(), fox_bets_messages)

for worker in workers:
    worker.join()
