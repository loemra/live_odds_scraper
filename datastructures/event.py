from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    id: str
    name: str
    sport: str
    date: datetime
    url: Optional[str] = field(default=None)

    def __post_init__(self):
        if type(self.date) is str:
            self.date = datetime.fromtimestamp(float(self.date))
        if type(self.date) is int:
            self.date = datetime.fromtimestamp(float(self.date))

    def __repr__(self) -> str:
        return (
            f"{self.sport}: {self.name} @"
            f" {self.date.strftime(r'%H:%M, %d-%m-%Y')}"
        )
