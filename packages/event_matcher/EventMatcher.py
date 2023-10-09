import json
from threading import Lock
from typing import List

import websocket

from ..data.Event import Event


class EventMatcher:
    def __init__(self, session_id, conversation):
        self.lock = Lock()
        self.ws = websocket.WebSocket()
        self.ws.connect(
            f"wss://umgpt.umich.edu/ws/t1/conversations/{conversation}/messages/",
            cookie=f"sessionid={session_id}",
        )
        self.conversation = conversation

    def _format_message(self, a, b):
        b = '["' + '", "'.join(b) + '"]'
        j = {
            "conversation": self.conversation,
            "text": f'"{a}" {b}',
            "role": "user",
        }
        return json.dumps(j)

    def _parse_results(self, r):
        j = json.loads(r)
        if j["text"] == "NO MATCH":
            return
        return int(j["text"])

    def match(self, sb_event: Event, unified_events: List[Event]):
        with self.lock:
            self.ws.send(
                self._format_message(
                    sb_event.name, [e.name for e in unified_events]
                )
            )
            # first one is just the message sent back.
            self.ws.recv()
            return self._parse_results(self.ws.recv())
