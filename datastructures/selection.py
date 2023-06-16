from dataclasses import dataclass


@dataclass
class Selection:
    id: str
    name: str
    odds: float

    def __str__(self) -> str:
        return self.name
