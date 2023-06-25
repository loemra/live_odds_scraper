from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Selection:
    id: str
    name: str
    odds: Optional[float]


@dataclass
class SportsbookSelection:
    selection: dict[str, Selection] = field(default_factory=dict)
