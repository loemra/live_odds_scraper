from dataclasses import dataclass, field
from datastructures.selection import Selection
from typing import Optional


@dataclass
class Market:
    id: str
    name: str
    code: str
    sub_type: Optional[str] = None
    selections: dict[str, Selection] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name
