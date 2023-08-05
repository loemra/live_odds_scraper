from sportsbooks.fanduel import fanduel
from util import logger_setup

logger_setup.setup()

for event in fanduel.get_events():
    print(event)
