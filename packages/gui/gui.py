import asyncio
import curses
import re
from asyncio import Lock, Queue, TaskGroup
from copy import deepcopy
from curses import wrapper
from curses.textpad import Textbox
from time import sleep

from pymongo.errors import PyMongoError

from packages.util.setup_logging import setup_logging
from packages.util.spawn import spawn

_logger = setup_logging(__name__)

# pretty sure i don't need this lock as i perform all _data operations
# "atomically" by never awaiting between important operations
# just want to be extra careful
_data_lock = asyncio.Lock()
_data_updated = asyncio.Event()
_data = {}


def run(db):
    _logger.info("running gui...")

    def wrapped(stdscr, db):
        asyncio.run(_run(db, stdscr))

    wrapper(wrapped, db)


async def _run(db, stdscr):
    async with TaskGroup() as tg:
        tg.create_task(_get_events(db))
        tg.create_task(_events_listener(db))
        tg.create_task(_odds_listener(db))
        tg.create_task(_draw(stdscr))


async def _get_events(db):
    _logger.info("getting events...")
    cur = db.unified_events.find()
    async for event in cur:
        _logger.info(f"handling event {event['_id']}")
        event_update = {"operationType": "insert", "fullDocument": event}
        await _handle_events_update(event_update)

    cur = db.market_odds.find()
    async for market_odds in cur:
        _logger.info(f"handling market {market_odds['_id']}")
        market_odds_update = {
            "operationType": "insert",
            "fullDocument": market_odds,
        }
        await _handle_odds_update(market_odds_update)


async def _events_listener(db, resume_token=None):
    pipeline = [{"$match": {"operationType": {"$in": ["insert", "delete"]}}}]
    while True:
        try:
            async with db.unified_events.watch(
                pipeline, resume_after=resume_token
            ) as stream:
                _logger.info("listening to updates...")
                async for update in stream:
                    resume_token = stream.resume_token
                    spawn(_handle_events_update(update))
        except PyMongoError as e:
            _logger.warning(f"Error with the stream, retrying now... {e}")


async def _handle_events_update(update):
    if update["operationType"] == "insert":
        event = update["fullDocument"]
        event_id = event["_id"]
        async with _data_lock:
            data_event = event.copy()
            data_event.pop("market_ids")
            data_event["market_odds"] = {}
            _data[event_id] = data_event
        _logger.info(f"handled new event {event_id}")

    elif update["operationType"] == "delete":
        event = update["fullDocument"]
        event_id = event["_id"]

        async with _data_lock:
            if event_id not in _data:
                _logger.warning(
                    f"receiving delete from untracked event {event_id}"
                )
                return

            _data.pop(event_id)
            _logger.info(f"handled new event {event_id}")

    _data_updated.set()


async def _odds_listener(db, resume_token=None):
    pipeline = [
        {"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}
    ]
    while True:
        try:
            async with db.market_odds.watch(
                pipeline, resume_after=resume_token
            ) as stream:
                _logger.info("listening to updates...")
                async for update in stream:
                    resume_token = stream.resume_token
                    spawn(_handle_odds_update(update))
        except PyMongoError as e:
            _logger.warning(f"Error with the stream, retrying now... {e}")


async def _handle_odds_update(update):
    if (
        update["operationType"] == "insert"
        or update["operationType"] == "update"
    ):
        market_odds = update["fullDocument"]
        event_id = market_odds["event_id"]
        market_id = market_odds["_id"]
        async with _data_lock:
            if event_id not in _data:
                _logger.warning(
                    "receiving odds updates for event that is not"
                    f" tracked for market {event_id}@{market_id}"
                )
                return

            _data[event_id]["market_odds"][market_id] = market_odds
            _logger.info(f"handled updated market {event_id}@{market_id}")

    elif update["operationType"] == "delete":
        market_odds = update["fullDocument"]
        event_id = market_odds["event_id"]
        market_id = market_odds["_id"]
        async with _data_lock:
            if event_id not in _data:
                _logger.warning(
                    "trying to delete odds for event that is not"
                    f" tracked for market {event_id}@{market_id}"
                )
                return

            if market_id not in _data[event_id]["markets"]:
                _logger.warning(
                    "trying to delete odds for market that is not tracked for"
                    f" market {event_id}@{market_id}"
                )
                return

            _data[event_id]["market_odds"].pop(market_id)
            _logger.info(f"handled deleted market {event_id}@{market_id}")

    _data_updated.set()


async def _draw(stdscr):
    # turn off cursor blinking
    curses.curs_set(0)
    curses.use_default_colors()

    # unblock getch
    stdscr.nodelay(True)

    keyword = ""
    page = 0

    def print_display(d):
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        search_box_offset = 2
        rows_per_page = h - 1 - search_box_offset

        nonlocal page
        page = min(page, len(d) // rows_per_page)

        start_row = page * rows_per_page
        end_row = start_row + rows_per_page
        for idx, row in enumerate(d[start_row:end_row], start_row):
            x = 5
            y = search_box_offset + idx - start_row + 1
            stdscr.addstr(y, x, row)
        # For the search box
        search_box_win = stdscr.subwin(1, 0)
        search_box_win.addstr(0, 0, "Search: " + keyword)
        stdscr.refresh()

    def handle_key(key):
        nonlocal keyword, page
        if key == curses.KEY_UP:
            if page > 0:
                page -= 1
        elif key == curses.KEY_DOWN:
            page += 1
        elif key in range(32, 127):
            keyword += chr(key)  # add entered character to the keyword
        elif key == 127:
            keyword = keyword[:-1]  # erase one character
        elif key == -1:
            return False

        return True

    new = True
    while True:
        if new:
            stdscr.clear()
            async with _data_lock:
                print_display(_stringify(_filter(_data, keyword)))

        await asyncio.sleep(0.01)
        key = stdscr.getch()
        new = handle_key(key) or _data_updated.is_set()


def _filter(data, search):
    filtered_data = deepcopy(data)
    if search == "":
        return filtered_data

    def search_dict(d, keys, s):
        try:
            for key in keys:
                if re.search(s, d[key], re.IGNORECASE):
                    return True
        except Exception:
            _logger.debug("invalid regex")
        return False

    # delimit by double spaces
    search_terms = search.split("  ")

    for event in data.values():
        event_search = search_terms[0]
        if not search_dict(event, ["name", "league"], event_search):
            filtered_data.pop(event["_id"])
            continue

        if len(search_terms) <= 1:
            continue
        market_search = search_terms[1]

        for market_odds in event["market_odds"].values():
            if not search_dict(market_odds, ["name", "kind"], market_search):
                filtered_data[event["_id"]]["market_odds"].pop(
                    market_odds["_id"]
                )
                continue

            if len(search_terms) <= 2:
                continue
            selection_search = search_terms[2]

            for i, selection in reversed(
                list(enumerate(market_odds["selections"]))
            ):
                if not search_dict(selection, ["name"], selection_search):
                    filtered_data[event["_id"]]["market_odds"][
                        market_odds["_id"]
                    ]["selections"].pop(i)
                    continue

                if len(search_terms) <= 3:
                    continue
                odds_search = search_terms[3]

                for j, odds in reversed(list(enumerate(selection["odds"]))):
                    if not search_dict(odds, ["sb"], odds_search):
                        filtered_data[event["_id"]]["market_odds"][
                            market_odds["_id"]
                        ]["selections"][i]["odds"].pop(j)
                        continue

                if (
                    len(
                        filtered_data[event["_id"]]["market_odds"][
                            market_odds["_id"]
                        ]["selections"][i]["odds"]
                    )
                    == 0
                ):
                    filtered_data[event["_id"]]["market_odds"][
                        market_odds["_id"]
                    ]["selections"].pop(i)

            if (
                len(
                    filtered_data[event["_id"]]["market_odds"][
                        market_odds["_id"]
                    ]["selections"]
                )
                == 0
            ):
                filtered_data[event["_id"]]["market_odds"].pop(
                    market_odds["_id"]
                )

        if len(filtered_data[event["_id"]]["market_odds"].keys()) == 0:
            filtered_data.pop(event["_id"])

    return filtered_data


def _stringify(data):
    if not data:
        return ""

    s = []
    for event in data.values():
        s.append(f"{event['name']}\n")

        for market_odds in event["market_odds"].values():
            s.append(f"\t{market_odds['name']}\n\n")

            selections_by_sb = {}
            s.append("".ljust(15))
            for selection in market_odds["selections"]:
                s.append(f"{selection['name']}".center(20))

                for odds in selection["odds"]:
                    if odds["sb"] not in selections_by_sb:
                        selections_by_sb[odds["sb"]] = []
                    selections_by_sb[odds["sb"]].append(odds["odds"])

            s.append("\n")

            for sb, odds in selections_by_sb.items():
                s.append(f"{sb}".ljust(15))
                for odd in odds:
                    s.append(f"{odd}".center(20))
                s.append("\n")
            s.append("\n")
        s.append("\n")
    return "".join(s).split("\n")
