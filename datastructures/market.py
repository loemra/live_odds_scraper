from datastructures.selection import SportsbookSelection
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
    sportsbook_selection: dict[str, SportsbookSelection] = field(default_factory=dict)
