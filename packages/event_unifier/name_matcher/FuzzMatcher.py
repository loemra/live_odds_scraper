import re

from thefuzz import fuzz, process

from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__)


async def match(
    to_be_matched,
    potential_matches,
    unable_to_determine,
    processor=lambda x: x,
    bad_score=60,
    good_score=80,
    logger=None,
):
    global _logger
    if logger is not None:
        _logger = logger

    if len(potential_matches) == 0:
        return None

    processed_to_be_matched = processor(to_be_matched)
    processed_potential_matches = [processor(x) for x in potential_matches]

    scores = process.extract(
        processed_to_be_matched,
        processed_potential_matches,
        scorer=_custom_scorer,
        limit=len(potential_matches),
    )

    res = None
    if scores[0][1] >= good_score:
        res = potential_matches[
            processed_potential_matches.index(scores[0][0])
        ]
        _logger.info(
            f"{processed_to_be_matched} matched @ {scores[0][0]} with score"
            f" {scores[0][1]}"
        )
    elif scores[0][1] > bad_score:
        _logger.info(
            f"unable to determine match for {processed_to_be_matched}"
        )
        res = await unable_to_determine(to_be_matched, potential_matches)
    else:
        _logger.info(
            f"{processed_to_be_matched} has no match"
        )

    if res is not None:
        return res


def _custom_scorer(query, choice):
    if (query.lower() == "tie" or query.lower() == "draw") and (
        choice.lower() == "tie" or choice.lower() == "draw"
    ):
        return 100

    qmatch = re.search(r"(?:\+|\-)?\d+", query)
    cmatch = re.search(r"(?:\+|\-)?\d+", choice)

    if ((qmatch is None) != (cmatch is None)) or (
        qmatch is not None
        and cmatch is not None
        and qmatch.group(0) != cmatch.group(0)
    ):
        return 0

    return fuzz.token_set_ratio(query, choice)
