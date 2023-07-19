from dataclasses import dataclass, field
from typing import Optional

from datastructures.market import Market


@dataclass
class Selection:
    id: str
    name: str
    link: str
    market: Market
    odds: Optional[float] = field(default=None)
