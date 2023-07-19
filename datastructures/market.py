from dataclasses import dataclass
from enum import Enum, auto


class MarketKind(Enum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()
    SPREAD = auto()


@dataclass(repr=True)
class Market:
    name: str
    period: str
    kind: MarketKind
