from dataclasses import dataclass, Field
from selection import Selection


@dataclass
class Market:
    id: str
    name: str
    code: str
    sub_type: str
    selections: dict[str, Selection] = Field(default_factory=dict)

    def __str__(self) -> str:
        return self.name
