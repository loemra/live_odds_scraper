import asyncio
import dataclasses
import json
import sys
import timeit
import traceback
from datetime import datetime

from packages.data.Event import Event
from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.db.DB import DB
from packages.db.MockDB import MockDB
from packages.name_matcher.FuzzMatcher import FuzzMatcher
from packages.name_matcher.MockMatcher import MockMatcher
from packages.name_matcher.NameMatcher import NameMatcher
from packages.sbs.betmgm.Betmgm import Betmgm
from packages.sbs.betrivers.Betrivers import Betrivers
from packages.sbs.draftkings.DraftKings import DraftKings
from packages.sbs.fanduel.Fanduel import Fanduel
from packages.sbs.pointsbet.PointsBet import PointsBet
from packages.util.logs import setup_root_logging, setup_seleniumwire_logging

with open("secrets.json", "r") as f:
    secrets = json.load(f)

setup_root_logging()
setup_seleniumwire_logging()


def test_name_matcher():
    em = NameMatcher(
        secrets["umgpt-session-id"], secrets["umgpt-conversation"], MockDB()
    )

    a = "SF Giants"
    b = "San Fran Warriors"
    c = "San Fran Giants"

    assert em.match(b, [a, c]) is None
    assert em.match(a, [b, c]) == 1

    e1 = "SF Giants vs. New York Yankees"
    s1_1 = "SF Giants -5.0"
    s1_2 = "New York Yankees +5.0"
    s2_1 = "Over"
    s2_2 = "Under"

    e2 = "New York Yankees versus San Francisco Giants"
    s3_1 = "San Francisco Giants"
    s3_2 = "New York Yankees"

    assert em.match(e1, [e2]) == 0
    assert em.match(s2_1, [s2_2]) is None
    assert em.match(s1_1, [s1_2, s2_1, s3_1, s3_2]) is None


def test_db():
    mm = MockMatcher()
    db = DB(secrets["test-db-name"])

    e1 = Event(
        "XEKJER",
        "SF Giants vs. New York Yankees",
        datetime.now(),
        Sport.BASEBALL,
        League.MLB,
    )

    m1 = Market(None, MarketName.SPREAD, Kind.H2H, line=5)
    s1_1 = Selection(1, "SF Giants -5.0")
    s1_2 = Selection(2, "New York Yankees +5.0")
    m1.selection.extend([s1_1, s1_2])

    m2 = Market(None, MarketName.TOTAL, Kind.OVER_UNDER, line=10)
    s2_1 = Selection(3, "Over")
    s2_2 = Selection(4, "Under")
    m2.selection.extend([s2_1, s2_2])

    e1.markets.extend([m1, m2])

    mm.inputs.extend([None] * 7)
    db.match_or_make_event(e1, "fox bets", mm)

    # matching event.
    e2 = Event(
        "SKDJ",
        "New York Yankees versus San Francisco Giants",
        datetime.now(),
        Sport.BASEBALL,
        League.MLB,
    )

    s1_3 = Selection("JAKDFSDFK", "NY Yankees 5.0")
    s1_4 = Selection("SDFLKJSDF", "SAN FRAN GIANTS -5.0")
    m1.selection = [s1_3, s1_4]

    m3 = Market(None, MarketName.MONEY_LINE, Kind.H2H)
    s3_1 = Selection(5, "San Francisco Giants")
    s3_2 = Selection(6, "New York Yankees")
    m3.selection.extend([s3_1, s3_2])

    e2.markets.extend([m1, m2, m3])

    mm.inputs.extend([0, 0, 1, 0, 0, 0, 1, None, None, None])
    db.match_or_make_event(e2, "bovada", mm)


def test_mgm():
    print("testing betmgm...")
    sb = Betmgm()

    for event, _ in sb.yield_events():
        print(f"{event.name} @ {event.league}, markets: {len(event.markets)}")


def test_mgm_odds():
    sb = Betmgm()

    async def tmp():
        async for update in sb.yield_odd_updates("v1|en-us|15122677|all"):
            print(update)

    asyncio.run(tmp())



def test_fanduel():
    print("testing fanduel...")
    sb = Fanduel()

    for event, _ in sb.yield_events():
        with open("logs/fanduel.out", "w") as f:
            d = dataclasses.asdict(event)
            d["date"] = d["date"].timestamp()
            json.dump(d, f)
        break


def test_betrivers():
    sb = Betrivers()

    for event, yield_odds_updates in sb.yield_events():
        print(event)


def test_draftkings():
    sb = DraftKings()

    for event, yield_odds_updates in sb.yield_events():
        print(event)


def test_pointsbet():
    sb = PointsBet()

    for event, yield_odds_updates in sb.yield_events():
        print(event)


def test_fuzz_matcher():
    fm = FuzzMatcher(MockDB())
    m = fm.match(
        "San Francisco 49ers @ Jacksonville Jaguars",
        ["San Francisco 49ers at Jacksonville Jaguars"],
    )
    print(f"m: {m}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        tests = [test_name_matcher, test_db, test_fanduel]
    else:
        tests = [eval(arg) for arg in sys.argv[1:]]

    for test in tests:
        try:
            time = timeit.timeit(test, number=1)
            print(f"{test.__qualname__} PASSED IN {time:.4f} S")
        except Exception as err:
            print(f"{test.__qualname__} FAILED {err}")
            traceback.print_exc()
