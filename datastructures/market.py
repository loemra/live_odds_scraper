from dataclasses import dataclass
from enum import StrEnum, auto


@dataclass
class MarketKind(StrEnum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()


@dataclass
class Market:
    name: str
    kind: MarketKind


@dataclass
class SbMarket:
    name: str
    market_id: str
    sb: str
