from dataclasses import dataclass, field
from datetime import datetime
from typing import Hashable, List

from packages.data.League import League
from packages.data.Market import Market

from .Sport import Sport


@dataclass
class Event:
    id: Hashable
    name: str
    date: datetime
    sport: Sport
    league: League
    markets: List[Market] = field(default_factory=list)

    @staticmethod
    def fromdb(id, name, date, sport, league):
        return Event(
            id, name, datetime.fromtimestamp(date), Sport(sport), League(league)
        )
