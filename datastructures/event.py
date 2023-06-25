from dataclasses import dataclass, field
from datetime import datetime
from market import Market


@dataclass
class EventMetadata:
    id: str
    name: str
    sport: str
    date: datetime

    def __repr__(self) -> str:
        return f"{self.sport}: {self.name} @ {self.date.strftime(r'%H:%M, %d-%m-%Y')}"

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "sport": self.sport,
            "date": self.date.timestamp(),
        }


@dataclass
class Event:
    metadata: EventMetadata
    markets: dict[str, Market] = field(default_factory=dict)
