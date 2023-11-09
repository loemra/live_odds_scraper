import json
from datetime import datetime
from threading import Lock, Timer

import websocket
from ratelimit import limits, sleep_and_retry
from ratelimit.exception import RateLimitException

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

        self._ping()

    def _ping(self):
        with self.lock:
            print(f"ping {datetime.now()}")
            j = {
                "conversation": self.conversation,
                "text": "ping",
                "role": "user",
            }
            self.ws.send(json.dumps(j).encode())
            self.ws.recv()
            self.ws.recv()

            Timer(10, self._ping).start()

    def _format_message(self, a, b):
        b = '["' + '", "'.join(b) + '"]'
        j = {
            "conversation": self.conversation,
            "text": f'"{a}" {b}',
            "role": "user",
        }
        return json.dumps(j).encode()

    def _parse_results(self, r):
        j = json.loads(r)
        if j["text"] == "You have reached your rate limit":
            raise RateLimitException(
                "rate limited by the website, waiting one minute...", 60
            )
        if j["text"] == "NO MATCH":
            return
        return int(j["text"])

    @sleep_and_retry
    @limits(calls=20, period=60)
    def match(self, to_be_matched, potential_matches):
        with self.lock:
            if len(potential_matches) == 0:
                return None
            self.ws.send(self._format_message(to_be_matched, potential_matches))
            # first one is just the message sent back.
            self.ws.recv()
            res = self._parse_results(self.ws.recv())

            print(f"{to_be_matched} matched @ {res} for {potential_matches}")

            matches = []
            for i, pm in enumerate(potential_matches):
                matches.append(
                    Match(to_be_matched, pm, res is not None and i == res)
                )
            self.db.record_match(matches)

            return res
