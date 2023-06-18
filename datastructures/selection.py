from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Selection:
    id: str
    name: str
    odds: float
    lock: Lock = field(default_factory=Lock)

    def __str__(self) -> str:
        return self.name
