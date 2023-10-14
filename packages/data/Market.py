from dataclasses import dataclass, field
from typing import Hashable, List, Optional

from packages.data.Kind import Kind
from packages.data.MarketName import MarketName
from packages.data.Period import Period
from packages.data.Selection import Selection


@dataclass
class Market:
    id: Optional[Hashable]
    name: MarketName
    kind: Kind
    period: Optional[Period] = field(default=None)
    participant: Optional[str] = field(default=None)
    line: Optional[float] = field(default=None)
    selection: List[Selection] = field(default_factory=list)

    @staticmethod
    def fromdb(id, name, kind, period, participant, line):
        p = None if period is None else Period(period)
        return Market(id, MarketName(name), Kind(kind), p, participant, line)
