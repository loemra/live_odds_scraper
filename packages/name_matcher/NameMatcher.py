import json
from threading import Lock

import websocket

from packages.data.Match import Match


class NameMatcher:
    def __init__(self, session_id, conversation, db):
        self.lock = Lock()
        self.ws = websocket.WebSocket()
        self.ws.connect(
            f"wss://umgpt.umich.edu/ws/t1/conversations/{conversation}/messages/",
            cookie=f"sessionid={session_id}",
        )
        self.conversation = conversation
        self.db = db

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

    def match(self, to_be_matched, potential_matches):
        with self.lock:
            self.ws.send(self._format_message(to_be_matched, potential_matches))
            # first one is just the message sent back.
            self.ws.recv()
            res = self._parse_results(self.ws.recv())

            matches = []
            for i, pm in enumerate(potential_matches):
                matches.append(
                    Match(to_be_matched, pm, res is not None and i == res)
                )
            self.db.record_match(matches)

            return res
