from dataclasses import dataclass
from datetime import datetime

from .Sport import Sport


@dataclass
class Event:
    id: int
    name: str
    date: datetime
    sport: Sport
