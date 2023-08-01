from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto
from typing import Optional


class Sport(StrEnum):
    SOCCER = auto()
    TENNIS = auto()


@dataclass
class Event:
    id: str
    name: str
    sport: Sport
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
