from datastructures.selection import Selection
from dataclasses import dataclass, field


@dataclass
class MarketMetadata:
    id: str


@dataclass
class Market:
    metadata: MarketMetadata
    selection: dict[str, Selection] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"{self.metadata.id}"
