from dataclasses import dataclass, field
from typing import Hashable, Mapping, Optional

from packages.data.Odds import Odds


@dataclass
class Selection:
    id: Hashable
    name: str
    odds: Optional[float] = field(default=None)
