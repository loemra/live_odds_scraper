from dataclasses import dataclass


@dataclass
class Update:
    event_id: str
    market_id: str
    selection_id: str
    new_odds: float
