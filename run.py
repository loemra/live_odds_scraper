import multiprocessing
from multiprocessing import Process

import events_updater
from sportsbooks.bovada import bovada
from sportsbooks.fox_bets import fox_bets

db_lock = multiprocessing.Lock()


def _handle_sb(sb: str, get_events, get_odds):
    events_updater.match_or_register_events(db_lock, sb, get_events)
    events_updater.update_or_register_event_selections(db_lock, sb, get_odds)


def run():
    args = [
        ("fox_bets", fox_bets.get_events, fox_bets.get_odds),
        ("bovada", bovada.get_events, bovada.get_odds),
    ]
    for arg in args:
        _handle_sb(*arg)
    # proc = []
    # for arg in args:
    #    p = Process(target=_handle_sb, args=arg)
    #    p.start()
    #    proc.append(p)

    # for p in proc:
    #    p.join()


if __name__ == "__main__":
    run()
