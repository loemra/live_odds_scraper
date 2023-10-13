from dataclasses import dataclass, field
from datetime import datetime
from typing import Sequence

from packages.data.Market import Market

from .Sport import Sport


@dataclass
class Event:
    id: int
    name: str
    date: datetime
    sport: Sport
    markets: Sequence[Market] = field(default_factory=list)

    @staticmethod
    def fromdb(id, name, date, sport):
        return Event(id, name, datetime.fromtimestamp(date), sport)
