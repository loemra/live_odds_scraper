from dataclasses import dataclass, asdict
from datetime import datetime


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
