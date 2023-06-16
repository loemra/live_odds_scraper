from threading import Thread
from sportsbook import Sportsbook

sportsbooks = {}
workers = []

def poll_get_messages(sportsbook, get_messages):
    for msg in get_messages():
        sportsbook.update_odds(msg)   

def register_sportsbook(name, get_messages):
    sportsbook = Sportsbook(name)
    sportsbooks[name] = sportsbook
    worker = Thread(target=poll_get_messages, args=(sportsbook, get_messages))
    worker.start()
    workers.append(worker)

from fox_bets import get_messages as fox_bets_messages
register_sportsbook('fox_bets', fox_bets_messages)

for worker in workers:
    worker.join()