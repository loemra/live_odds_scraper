from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from datastructures.market import Market


@dataclass
class EventMetadata:
    id: str
    name: str
    sport: str
    date: datetime
    url: Optional[str] = field(default=None)

    def __repr__(self) -> str:
        return (
            f"{self.sport}: {self.name} @"
            f" {self.date.strftime(r'%H:%M, %d-%m-%Y')}"
        )


@dataclass
class Event:
    metadata: EventMetadata
    markets: dict[str, Market] = field(default_factory=dict)
