from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from datastructures.selection import Selection


class Name(Enum):
    TOTAL_GOALS = auto()


class Kind(Enum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()
    SPREAD = auto()


class Period(Enum):
    REGULAR = auto()
    FIRST_HALF = auto()
    SECOND_HALF = auto()


@dataclass
class Market:
    id: str
    name: Name
    kind: Kind
    period: Period
    player: Optional[str] = field(default=None)
    line: Optional[float] = field(default=None)

    selection: list[Selection] = field(default_factory=list)

    def __post_init__(self):
        if self.line is not None:
            if type(self.line) is str:
                self.line = float(self.line)
            elif type(self.line) is not float:
                # TODO: universal logger...
                pass
