import json
import os
from asyncio import Queue

import websockets
from tenacity import retry, stop_after_attempt, wait_exponential

from packages.util.setup_logging import setup_logging
from packages.util.spawn import spawn

_logger = setup_logging(__name__)
_session_id = os.getenv("UMGPT_SESSION_ID")
_conversation = os.getenv("UMGPT_CONVERSATION_ID")

_key_to_text = {}
_text_to_queue = {}
_producer_queue = Queue()

_running = False


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=60, max=120))
async def match(
    to_be_matched, potential_matches, processor=lambda x: x, logger=None
):
    global _logger
    if logger is not None:
        _logger = logger

    if len(potential_matches) == 0:
        return None

    global _running
    if not _running:
        spawn(_runner())
        _running = True

    text = _format_message(
        processor(to_be_matched), [processor(x) for x in potential_matches]
    )

    q = Queue()
    _text_to_queue[text] = q

    await _producer_queue.put(text)
    res = await q.get()

    return (
        potential_matches[index]
        if (index := _parse_results(res)) is not None
        else None
    )


def _format_message(a, b):
    b = '["' + '", "'.join(b) + '"]'
    j = {
        "conversation": _conversation,
        "text": f'"{a}" {b}',
        "role": "user",
    }
    return json.dumps(j).encode()


def _parse_results(r):
    j = json.loads(r)
    if j["text"] == "You have reached your rate limit":
        raise Exception("rate limited")
    if j["text"] == "NO MATCH":
        return
    return int(j["text"])


async def _runner():
    async for ws in websockets.connect(
        f"wss://umgpt.umich.edu/ws/t1/conversations/{_conversation}/messages/",
        cookie=f"sessionid={_session_id}",
    ):
        try:
            spawn(_consumer(ws))
            spawn(_producer(ws))
        except websockets.ConnectionClosed:
            continue


async def _consumer(ws):
    while True:
        data = await ws.recv()
        _logger.debug(f"received {data}")
        j = json.loads(data)
        if j["role"] == "user":
            _key_to_text[j["id"] + 1] = j["text"]
            continue

        if not (text := _key_to_text.get(j["id"])):
            _logger.debug(f"could not find text from key... {j['id']}")
            continue

        _key_to_text.pop(j["id"])

        if not (q := _text_to_queue.get(text)):
            _logger.debug(f"could not find queue from text... {text}")
            continue

        spawn(q.put(j["text"]))


async def _producer(ws):
    while True:
        text = await _producer_queue.get()
        _logger.debug(f"sending {text}")
        spawn(ws.send(text))
