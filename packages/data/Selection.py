from dataclasses import dataclass, field
from typing import Hashable, Mapping

from packages.data.Odds import Odds


@dataclass
class Selection:
    id: int
    name: str
    odds: Mapping[Hashable, Odds] = field(default_factory=dict)
