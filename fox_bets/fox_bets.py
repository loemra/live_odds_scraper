from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection
from fox_bets.config import get_events_urls, get_event_url
import requests
from datetime import datetime


def _parse_events(j) -> list[EventMetadata]:
    events = []
    for league in j:
        for event in league["event"]:
            date = datetime.fromtimestamp(float(event["eventTime"]) / 1000)
            events.append(
                EventMetadata(event["id"], event["name"], event["sport"], date)
            )
    return events


def _parse_odds(j) -> list[Market]:
    markets = []
    for market in j["markets"]:
        metadata = MarketMetadata(market["type"])
        m = Market(metadata)
        for selection in market["selection"]:
            id = selection["id"]
            try:
                odds = {"fox_bets": float(selection["odds"]["dec"])}
            except ValueError:
                odds = {}
            m.selection[id] = Selection(id, selection["name"], odds)
        markets.append(m)
    return markets


def _get_events(events_url: str):
    result = requests.get(events_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_events(): status code = {result.status_code}, url ="
            f" {events_url}, text = {result.text}"
        )
    return result.json()


def _get_event(event_url: str):
    result = requests.get(event_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_event(): status code = {result.status_code}, url ="
            f" {event_url}, text = {result.text}"
        )
    return result.json()


# gets all upcoming events for fox_bets and returns: event name, sport, time, and fox_bet_event_id.
def get_events(date: datetime) -> list[EventMetadata]:
    events = []
    for event_url in get_events_urls(date):
        events.extend(_parse_events(_get_events(event_url)))
    return events


# gets initial odds for an upcoming event given fox_bet_event_id.
def get_odds(event_id: str, sport: str) -> list[Market]:
    return _parse_odds(_get_event(get_event_url(event_id, sport)))


# return a generator that will yield update_msgs.
def register_for_live_odds_updates(id):
    pass


"""
import requests
import websocket
import json
import time
import threading

from logs import logger
from fox_bets.config import config


# GET LIVE EVENTS
def _get_live_events():
    logger.info("Getting live events...")
    result = requests.get(config["live_events"]["url"])
    if result.status_code != 200:
        logger.error(
            f"get_live_events status code: {result.status_code}\nresult: {result.text}"
        )
        exit(-1)
    logger.info("Success: got live events")
    return result.json()


def _get_event_id_and_sport_from_live_events(j):
    info = []
    for o in j:
        events = o["inplay"]["event"]
        for event in events:
            info.append((event["id"], event["sport"]))
    return info


def _get_live_markets_for_sports(sports):
    markets = []
    for sport in sports:
        markets.append(
            ",".join(config["markets_for_sports"][sport]["keyMarkets"]["inplay"])
        )
    return markets


def generate_payloads():
    event_ids, sports = map(
        list, zip(*_get_event_id_and_sport_from_live_events(live_events))
    )
    markets = _get_live_markets_for_sports(sports)
    payloads = []
    for event_id, market in zip(event_ids, markets):
        payload = config["subscribe"]["payload"]
        payload["UpdateSubcriptions"]["toAdd"][0]["ids"] = event_id
        payload["UpdateSubcriptions"]["toAdd"][1]["ids"] = market
        payloads.append(json.dumps(payload))
    return payloads


# SOCKET SETUP
def _setup_send_alive(ws):
    def _send_alive_request_background():
        while True:
            time.sleep(10)
            logger.info("Keep alive request")
            ws.send(config["socket"]["send_alive"])

    threading.Thread(target=_send_alive_request_background, daemon=True).start()


def get_socket():
    logger.info("Making socket...")
    url, payload = config["socket"]["url"], config["socket"]["payload"]
    ws = websocket.WebSocket(enable_multithread=True)
    ws.connect(url)
    ws.send(payload)
    response = ws.recv()
    if "error" in response:
        logger.error(f"Authentication Error: {response}")
        exit(-1)
    logger.info("Success: Made socket")
    _setup_send_alive(ws)
    return ws


def send_subscribe_payloads(payloads):
    logger.info(f"Sending {len(payloads)} subscribe payloads...")
    logger.debug(f"Payloads sent: {payloads}")
    for payload in payloads:
        ws.send(payload)


# MESSAGE HANDLING
def _handle_message(msg):
    if "error" in msg:
        logger.error("handle message error: {}".format(msg))
        return

    if "Response" in msg:
        logger.info("Keep alive response: {}".format(msg))
        return

    if "sr" in msg:
        logger.info(f"Subscribe Response! {msg}")

    return json.loads(msg)


def _initial_setup():
    logger.info("Running initial setup for fox_bets scraper.")
    global ws
    ws = get_socket()

    global live_events
    live_events = _get_live_events()

    payloads = generate_payloads()
    send_subscribe_payloads(payloads)

    global _setup
    _setup = True


_initial_setup()


# PUBLIC FACING
def get_messages():
    while True:
        yield _handle_message(ws.recv())


if __name__ == "__main__":
    with open("messages.json", "w") as f:
        for message in get_messages():
            json.dump(message, f)          
"""
