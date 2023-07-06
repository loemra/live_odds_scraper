# SOCKETS
def _setup_send_alive(ws):
    def _send_alive_request_background():
        while True:
            time.sleep(10)
            ws.send(config.get_send_alive())

    threading.Thread(target=_send_alive_request_background, daemon=True).start()


def _get_socket():
    url, payload = config.get_url_and_auth_payload()
    ws = websocket.WebSocket(enable_multithread=True)
    ws.connect(url)
    ws.send(payload.encode())
    response = ws.recv()
    if "error" in response:
        raise Exception("Unable to start fox_bets socket.")
    _setup_send_alive(ws)
    return ws


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
                odds = config.get_ri_odds(selection["ri"])
            except KeyError as err:
                print(
                    f"error: {err}\nno selection_id or no odds in"
                    f" selection: {selection}"
                )
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


def register_for_live_odds_updates(
    event_id: str, markets: list[MarketMetadata]
):
    global ws
    if not ws:
        ws = _get_socket()

    payload = config.get_subscribe_payload(event_id, markets)
    ws.send(payload.encode())
