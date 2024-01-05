from packages.util.setup_logging import setup_logging

_logger = setup_logging(__name__)


def gen(res):
    for r in res:
        yield r


async def match(g, to_be_matched, potential_matches, processor):
    try:
        n = next(g)

        def tmp():
            if n is None:
                return
            return potential_matches[n]

        _logger.info(
            f"result for {processor(to_be_matched)}:\n"
            f" {[processor(p) for p in potential_matches]} matched at {n}"
        )
        return tmp()
    except StopIteration:
        _logger.debug(
            f"no result for {processor(to_be_matched)}:\n"
            f" {[processor(p) for p in potential_matches]}"
        )
