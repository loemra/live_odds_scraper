from multiprocessing import Process

import events_updater
from sportsbooks.bovada import bovada
from sportsbooks.fox_bets import fox_bets


def _handle_sb(sb: str, get_events, get_odds):
    events_updater.match_or_register_events(sb, get_events)
    events_updater.update_or_register_event_selections(sb, get_odds)


def run():
    args = [
        ("fox_bets", fox_bets.get_events, fox_bets.get_odds),
        ("bovada", bovada.get_events, bovada.get_odds),
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
