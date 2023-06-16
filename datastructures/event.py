from dataclasses import dataclass, Field
from market import Market


@dataclass
class Event:
    id: str
    name: str
    sport: str
    markets: dict[str, Market] = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.name
