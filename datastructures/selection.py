from dataclasses import dataclass, field
from typing import Optional


@dataclass(repr=True)
class Selection:
    id: str
    name: str
    link: str
    market_id: str
    odds: Optional[float] = field(default=None)
