import database.translaters.translater as translater
import fox_bets.fox_bets as fox_bets
from database.events_database import get_events, get_markets, update_event_odds
from datastructures.event import EventMetadata
from datastructures.market import MarketMetadata
from datastructures.update import Update


def get_live_events() -> list[EventMetadata]:
    # TODO: actually get the live events.
    return get_events()


for event in get_live_events():
    fox_bets_event_id = translate_event_id_to_sportsbook("fox_bets", event.id)
    markets = []
    for market in get_markets(event.id):
        market_code = translate_market_to_sportsbook("fox_bets", market.code)
        markets.append(MarketMetadata(market_code))
    fox_bets.register_for_live_odds_updates(fox_bets_event_id, markets)

for update in fox_bets.get_updates():
    unified_event_id = translate_event_id("fox_bets", update.event_id)
    unified_market_code = translate_market("fox_bets", update.market_code)
    unified_selection_id = translate_selection_id("fox_bets", update.selection_id)

    if unified_event_id and unified_market_code and unified_selection_id:
        update_event_odds(
            Update(
                unified_event_id,
                unified_market_code,
                unified_selection_id,
                update.new_odds,
            )
        )
