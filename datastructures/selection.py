from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Selection:
    id: str
    name: str
    odds: Optional[float] = field(default=None)

    def __post_init__(self):
        if self.odds is not None:
            if type(self.odds) is str:
                self.odds = float(self.odds)
            elif type(self.odds) is not float:
                # TODO: global logger.
                pass
