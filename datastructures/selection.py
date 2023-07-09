from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Selection:
    id: str
    name: str
    link: str
    market_id: str
    odds: Optional[float] = field(default=None)

    def __repr__(self) -> str:
        return f"{self.name} odds: {self.odds}"
