from dataclasses import dataclass


@dataclass
class Selection:
    id: str
    name: str
    odds: float
