import json
import timeit
from datetime import datetime

from packages.data.Event import Event
from packages.data.Sport import Sport
from packages.event_matcher.EventMatcher import EventMatcher

with open("secrets.json", "r") as f:
    secrets = json.load(f)


def test_event_matcher():
    em = EventMatcher(
        secrets["umgpt-session-id"], secrets["umgpt-conversation"]
    )

    a = Event(1, "SF Giants", datetime.now(), Sport.SOCCER)
    b = Event(1, "San Fran Warriors", datetime.now(), Sport.SOCCER)
    c = Event(1, "San Fran Giants", datetime.now(), Sport.SOCCER)

    assert em.match(b, [a, c]) is None
    assert em.match(a, [b, c]) == 1


if __name__ == "__main__":
    tests = [test_event_matcher]
    for test in tests:
        try:
            time = timeit.timeit(test, number=1)
            print(f"{test.__qualname__} PASSED IN {time:.4f} S")
        except Exception as err:
            print(f"{test.__qualname__} FAILED {err}")
