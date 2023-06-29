from dataclasses import dataclass, field


@dataclass
class SelectionMetadata:
    id: str
    name: str

    def __repr__(self) -> str:
        return self.name


@dataclass
class Selection:
    metadata: SelectionMetadata
    odds: dict[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"{self.metadata} odds: {self.odds}"
