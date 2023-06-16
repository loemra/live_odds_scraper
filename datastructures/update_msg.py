from dataclasses import dataclass


# this is the payload that will be sent to a sportsbook when there is an update.
@dataclass
class UpdateMsg:
    event_id: str
    market_id: str
    selection_id: str
    new_odds: float
