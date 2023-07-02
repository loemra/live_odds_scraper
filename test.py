from datetime import datetime

from bovada import bovada

print(bovada.get_events(datetime.today()))
