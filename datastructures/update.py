from dataclasses import dataclass


@dataclass
class Update:
    event_id: str
    market_code: str
    selection_id: str
    new_odds: float
