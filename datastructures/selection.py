from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Selection:
    id: str
    name: str
    odds: dict[str, float] = field(default_factory=dict)
