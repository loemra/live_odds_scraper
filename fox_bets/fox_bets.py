import json
import threading
import time
from datetime import datetime

import requests
import websocket

from datastructures.event import EventMetadata
from datastructures.market import Market, MarketMetadata
from datastructures.selection import Selection, SelectionMetadata
from datastructures.update import Update
from fox_bets.config import (get_event_url, get_events_urls, get_ri_odds,
                             get_send_alive, get_subscribe_payload,
                             get_url_and_auth_payload)


def _parse_events(j) -> list[EventMetadata]:
    events = []
    for league in j:
        for event in league["event"]:
            date = datetime.fromtimestamp(float(event["eventTime"]) / 1000)
            events.append(EventMetadata(event["id"], event["name"], event["sport"], date))
    return events


def _parse_odds(j) -> list[Market]:
    markets = []
    for market in j["markets"]:
        if market.get("mostBalanced") is not None and market["mostBalanced"] == False:
            continue
        metadata = MarketMetadata(market["type"])
        m = Market(metadata)
        for selection in market["selection"]:
            id = selection["id"]
            try:
                odds = {"fox_bets": float(selection["odds"]["dec"])}
            except ValueError:
                odds = {}
            m.selection[id] = Selection(SelectionMetadata(id, selection["name"]), odds)
        markets.append(m)
    return markets


def _get_events(events_url: str):
    result = requests.get(events_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_events(): status code = {result.status_code}, url =" f" {events_url}, text = {result.text}"
        )
    return result.json()


def _get_event(event_url: str):
    result = requests.get(event_url)
    if not result.status_code == 200:
        raise Exception(
            f"fox_bets: _get_event(): status code = {result.status_code}, url =" f" {event_url}, text = {result.text}"
        )
    return result.json()


# SOCKETS
def _setup_send_alive(ws):
    def _send_alive_request_background():
        while True:
            time.sleep(10)
            ws.send(get_send_alive())

    threading.Thread(target=_send_alive_request_background, daemon=True).start()


def _get_socket():
    url, payload = get_url_and_auth_payload()
    ws = websocket.WebSocket(enable_multithread=True)
    ws.connect(url)
    ws.send(payload.encode())
    response = ws.recv()
    if "error" in response:
        raise Exception("Unable to start fox_bets socket.")
    _setup_send_alive(ws)
    return ws


# gets all upcoming events for fox_bets and returns: event name, sport, time, and fox_bet_event_id.
def get_events(date: datetime) -> list[EventMetadata]:
    events = []
    for event_url in get_events_urls(date):
        events.extend(_parse_events(_get_events(event_url)))
    return events


# gets initial odds for an upcoming event given fox_bet_event_id.
def get_odds(event_id: str, sport: str) -> list[Market]:
    return _parse_odds(_get_event(get_event_url(event_id, sport)))


def _handle_sr(msg):
    for m in msg["sr"]["mdl"]:
        try:
            yield m["ets"]
        except (KeyError, TypeError) as err:
            pass
            # print(f"Key error:{err}\n\ttrying to _get_etss for SR message: {msg}")


def _get_etss(msg):
    try:
        msg["sr"]["mdl"]
        for ets in _handle_sr(msg):
            yield ets
        return
    except (KeyError, TypeError) as err:
        pass

    try:
        yield msg["pm"]["ets"]
    except (KeyError, TypeError) as err:
        pass
        # print(f"Key error:{err}\n\ttrying to _get_etss for PM message: {msg}")


def _create_update_msgs(ets):
    try:
        event_id = ets["i"]
        markets = ets["ml"]
    except KeyError as err:
        print(f"error: {err}\nets has no event_id or no markets in ets: {ets}")
        return

    for market in markets:
        try:
            market_code = market["t"]
            selections = market["sl"]
        except KeyError as err:
            # print(f"error: {err}\nno market_id or no selections in market: {market}")
            continue

        for selection in selections:
            try:
                selection_id = selection["i"]
                odds = get_ri_odds(selection["ri"])
            except KeyError as err:
                print(f"error: {err}\nno selection_id or no odds in" f" selection: {selection}")
                continue

            yield Update(event_id, market_code, selection_id, "fox_bets", odds)


def _parse_msg(msg: str):
    if "error" in msg:
        return
    if "Response" in msg:
        return

    if "sr" in msg:
        # logger.info(f"Subscribe Response! {msg}")
        pass

    for ets in _get_etss(json.loads(msg)):
        for update in _create_update_msgs(ets):
            yield update


ws = None


def get_updates():
    global ws
    if not ws:
        ws = _get_socket()

    while True:
        for update in _parse_msg(ws.recv()):
            if not update:
                continue
            yield update


def register_for_live_odds_updates(event_id: str, markets: list[MarketMetadata]):
    global ws
    if not ws:
        ws = _get_socket()

    payload = get_subscribe_payload(event_id, markets)
    ws.send(payload.encode())
