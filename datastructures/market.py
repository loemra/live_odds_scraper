from dataclasses import dataclass
from enum import StrEnum, auto


@dataclass
class MarketKind(StrEnum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()
