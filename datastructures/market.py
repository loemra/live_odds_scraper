from datastructures.selection import Selection
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MarketMetadata:
    code: str
    # name: str
    # sub_type: Optional[str]


@dataclass
class Market:
    metadata: MarketMetadata
    selection: dict[str, Selection] = field(default_factory=dict)
