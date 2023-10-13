from dataclasses import dataclass, field
from typing import Hashable, Mapping

from packages.data.Kind import Kind
from packages.data.Period import Period
from packages.data.Selection import Selection


@dataclass
class Market:
    id: int | None
    name: str
    kind: Kind
    period: Period
    participant: str
    line: float
    selection: Mapping[Hashable, Selection] = field(default_factory=dict)

    @staticmethod
    def fromdb(id, name, kind, period, participant, line):
        return Market(id, name, Kind[kind], Period[period], participant, line)
