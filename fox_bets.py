import fox_bets_scraper as fox_bets_scraper
# from  import logger

def _translate(msg):
    pass

# PUBLIC FACING
def get_messages():
    for msg in fox_bets_scraper.get_messages():
        yield _translate(msg)