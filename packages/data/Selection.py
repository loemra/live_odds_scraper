from dataclasses import dataclass, field
from typing import Hashable, Mapping

from packages.data.Odds import Odds


@dataclass
class Selection:
    id: Hashable
    name: str
    odds: Mapping[Hashable, Odds] = field(default_factory=dict)
