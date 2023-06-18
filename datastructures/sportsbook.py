from dataclasses import dataclass, field
from datastructures.event import Event
from datastructures.update_msg import UpdateMsg
from logs import logger


@dataclass
class Sportsbook:
    name: str
    events: dict[str, Event] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name

    def update_odds(self, update_msg: UpdateMsg):
        try:
            event = self.events[update_msg.event_id]
        except KeyError as ke:
            logger.debug(f"Unable to find event for event_id: {update_msg.event_id}")
            return

        try:
            market = event.markets[update_msg.market_id]
        except KeyError as ke:
            logger.debug(
                f"Unable to find market for event: {event}, market_id:"
                f" {update_msg.market_id}"
            )
            return

        try:
            selection = market.selections[update_msg.selection_id]
        except KeyError as ke:
            logger.debug(
                f"Unable to find selection for event: {event}, market_id:"
                f" {update_msg.market_id}, selection_id: {update_msg.selection_id}"
            )
            return

        with selection.lock:
            logger.info(
                f"Updating odds for {self.name}/{event}/{market}/{selection} from"
                f" {selection.odds} to {update_msg.new_odds}"
            )
            print(
                f"Updating odds for {self.name}/{event}/{market}/{selection} from"
                f" {selection.odds} to {update_msg.new_odds}"
            )
            selection.odds = update_msg.new_odds
