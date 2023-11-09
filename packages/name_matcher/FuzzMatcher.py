import re
from threading import Lock

from thefuzz import fuzz, process

from packages.data.Match import Match
from packages.util.logs import setup_logging


class FuzzMatcher:
    def __init__(self, db, bad_score=60, good_score=80, fallback_matcher=None):
        self.lock = Lock()
        self.db = db
        self.bad_score = bad_score
        self.good_score = good_score
        self.fallback_matcher = fallback_matcher
        self.logger = setup_logging(__name__, False)

    def _custom_scorer(self, query, choice):
        if (query.lower() == "tie" or query.lower() == "draw") and (
            choice.lower() == "tie" or choice.lower() == "draw"
        ):
            return 100

        qmatch = re.search(r"(?:\+|\-)?\d+", query)
        cmatch = re.search(r"(?:\+|\-)?\d+", choice)

        if qmatch is None != cmatch is None or (
            qmatch is not None
            and cmatch is not None
            and qmatch.group(0) != cmatch.group(0)
        ):
            return 0

        return fuzz.token_set_ratio(query, choice)

    def match(self, to_be_matched, potential_matches):
        if len(potential_matches) == 0:
            return None

        ress = process.extract(
            to_be_matched,
            potential_matches,
            scorer=self._custom_scorer,
            limit=len(potential_matches),
        )

        res = None
        if ress[0][1] >= self.good_score:
            res = potential_matches.index(ress[0][0])
        elif ress[0][1] > self.bad_score and self.fallback_matcher is not None:
            res = self.fallback_matcher.match(to_be_matched, potential_matches)

        self.logger.info(
            f"{to_be_matched} matched @ {res} for {potential_matches} with"
            f" scores {ress}"
        )

        matches = []
        for i, pm in enumerate(potential_matches):
            matches.append(
                Match(to_be_matched, pm, res is not None and i == res)
            )
        self.db.record_match(matches)

        return res
