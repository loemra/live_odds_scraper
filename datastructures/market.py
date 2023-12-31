from dataclasses import dataclass, field
from enum import Enum, StrEnum, auto
from typing import Optional

from datastructures.selection import Selection


class Name(StrEnum):
    SOCCER_GAME_RESULT = auto()
    SOCCER_OVER_UNDER_TOTAL_GOALS = auto()
    SOCCER_BOTH_TEAMS_TO_SCORE = auto()
    TENNIS_GAME_SPREAD = auto()
    TENNIS_OVER_UNDER_TOTAL_GAMES = auto()
    TENNIS_HEAD_TO_HEAD = auto()


class Kind(StrEnum):
    TEAM_NAME = auto()
    OVER_UNDER = auto()
    YES_NO = auto()
    SPREAD = auto()


class Period(StrEnum):
    REGULAR = auto()
    FIRST_HALF = auto()
    SECOND_HALF = auto()

    MATCH = auto()
    FIRST_SET = auto()
    SECOND_SET = auto()


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
