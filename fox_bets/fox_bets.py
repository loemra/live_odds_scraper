import fox_bets.scraper as scraper
from logs import logger


def _translate(msg):
    return msg


# PUBLIC FACING
def get_messages():
    for msg in scraper.get_messages():
        yield _translate(msg)
