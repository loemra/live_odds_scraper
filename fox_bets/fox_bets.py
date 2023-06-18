import fox_bets.scraper as scraper
from fox_bets.config import get_odds
from logs import logger
from datastructures.update_msg import UpdateMsg
from datastructures.sportsbook import Sportsbook
from datastructures.event import Event
from datastructures.market import Market
from datastructures.selection import Selection


def _handle_sr(msg):
    for m in msg["sr"]["mdl"]:
        try:
            yield m["ets"]
        except (KeyError, TypeError) as err:
            logger.debug(
                f"Key error:{err}\n\ttrying to _get_etss for SR message: {msg}"
            )


# TODO: Look into pm.ev
def _get_etss(msg):
    try:
        msg["sr"]["mdl"]
        for ets in _handle_sr(msg):
            yield ets
        return
    except (KeyError, TypeError) as err:
        pass

    try:
        yield msg["pm"]["ets"]
    except (KeyError, TypeError) as err:
        logger.debug(f"Key error:{err}\n\ttrying to _get_etss for PM message: {msg}")


def _create_update_msgs(ets):
    try:
        event_id = ets["i"]
        markets = ets["ml"]
    except KeyError as err:
        logger.debug(f"error: {err}\nets has no event_id or no markets in ets: {ets}")
        return

    for market in markets:
        try:
            market_id = market["i"]
            selections = market["sl"]
        except KeyError as err:
            logger.debug(
                f"error: {err}\nno market_id or no selections in market: {market}"
            )
            continue

        for selection in selections:
            try:
                selection_id = selection["i"]
                odds = get_odds(selection["ri"])
            except KeyError as err:
                logger.debug(
                    f"error: {err}\nno selection_id or no odds in"
                    f" selection: {selection}"
                )
                continue

            yield UpdateMsg(event_id, market_id, selection_id, odds)


def _translate(msg):
    for ets in _get_etss(msg):
        for update_msg in _create_update_msgs(ets):
            yield update_msg


def _parse_live_events(live_events) -> Sportsbook:
    sb = Sportsbook("fox_bets")
    for o in live_events:
        try:
            events = o["inplay"]["event"]
        except KeyError as err:
            logger.debug(f"error: {err}\ninvalid event for live_events: {o}")
            continue
        for event in events:
            try:
                event_id = event["id"]
                event_name = event["name"]
                event_sport = event["sport"]
                markets = event["markets"]
            except KeyError as err:
                logger.debug(f"error: {err}\nunable to parse event: {event}")
                continue

            event = Event(event_id, event_name, event_sport)

            for market in markets:
                try:
                    market_id = market["id"]
                    market_name = market["name"]
                    market_code = market["type"]
                    market_subtype = market["subtype"] if "subtype" in market else None
                    selections = market["selection"]
                except KeyError as err:
                    logger.debug(f"error: {err}\nunable to parse market: {market}")
                    continue

                market = Market(market_id, market_name, market_code, market_subtype)

                for selection in selections:
                    try:
                        selection_id = selection["id"]
                        selection_name = selection["name"]
                        odds = get_odds(selection["odds"]["rootIdx"])
                    except KeyError as err:
                        logger.debug(
                            f"error: {err}\nunable to parse selection: {selection}"
                        )
                        continue

                    selection = Selection(selection_id, selection_name, odds)
                    market.selections[selection_id] = selection
                event.markets[market_id] = market
            sb.events[event_id] = event
    return sb


# PUBLIC FACING
def get_messages():
    for msg in scraper.get_messages():
        for update_msg in _translate(msg):
            yield update_msg


def make_sportsbook() -> Sportsbook | None:
    live_events = scraper.live_events
    if not live_events:
        logger.error("No live_events for fox_bets!")
        return None
    return _parse_live_events(live_events)
