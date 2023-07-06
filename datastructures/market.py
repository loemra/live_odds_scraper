from dataclasses import dataclass, field
from enum import StrEnum, auto

from datastructures.selection import Selection


@dataclass
class MarketKind(StrEnum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()


@dataclass
class MarketMetadata:
    id: str
    kind: MarketKind


@dataclass
class Market:
    metadata: MarketMetadata
    selection: dict[str, Selection] = field(default_factory=dict)
    linked: list[list[str]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.metadata.id}/{self.metadata.kind}"
