from dataclasses import dataclass, field
from datastructures.market import Market


@dataclass
class Event:
    id: str
    name: str
    sport: str
    markets: dict[str, Market] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name
