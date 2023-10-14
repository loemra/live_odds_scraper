from dataclasses import dataclass
from datetime import datetime
from typing import Hashable


@dataclass
class OddsUpdate:
    id: Hashable
    sb: str
    odds: float
    time: datetime
