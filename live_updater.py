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
    event_id = translater.unified_to_sportsbook_event_id("fox_bets", event.id)
    print(event.id)
    if not event_id:
        continue
    markets = []
    for market in get_markets(event.id):
        market_code = translater.unified_to_sportsbook_market_id("fox_bets", market.id)
        if not market_code:
            continue
        markets.append(MarketMetadata(market_code))
    fox_bets.register_for_live_odds_updates(event_id, markets)

for update in fox_bets.get_updates():
    unified_event_id = translater.sportsbook_to_unified_event_id("fox_bets", update.event_id)
    unified_market_code = translater.sportsbook_to_unified_market_id("fox_bets", update.market_id)
    unified_selection_id = translater.sportsbook_to_unified_selection_id("fox_bets", update.selection_id)

    if unified_event_id and unified_market_code and unified_selection_id:
        update_event_odds(
            Update(
                unified_event_id,
                unified_market_code,
                unified_selection_id,
                update.new_odds,
            )
        )
