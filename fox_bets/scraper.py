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
    live_events = _get_live_events()
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

    return json.loads(msg)


# PUBLIC FACING
def get_messages():
    global ws
    ws = get_socket()

    payloads = generate_payloads()
    send_subscribe_payloads(payloads)

    while True:
        yield _handle_message(ws.recv())


if __name__ == "__main__":
    with open("messages.json", "w") as f:
        for message in get_messages():
            json.dump(message, f)
