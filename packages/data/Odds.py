from dataclasses import dataclass
from typing import Hashable


@dataclass
class Odds:
    id: Hashable
    sb: str
    odds: float
