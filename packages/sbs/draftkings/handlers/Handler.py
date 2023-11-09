from datetime import datetime
from itertools import chain

import requests

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.util.logs import setup_logging


class Handler:
    def __init__(self, event_group, sport: Sport, league: League):
        self.event_group = event_group
        self.sport = sport
        self.league = league
        self.logger = setup_logging(__name__)

    def yield_events(self):
        events = self._get_events()
        for event in self._iterate_events(events):
            markets = self._get_markets(event.id)
            for j, market in self._iterate_markets(markets):
                for selection in self._iterate_selections(j):
                    market.selection.append(selection)
                event.markets.append(market)
            yield event

    def _get_events(self):
        r = requests.get(
            f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/{self.event_group}?format=json"
        )
        return r.json()

    def _get_markets(self, eventID):
        r = requests.get(
            f"https://sportsbook-us-mi.draftkings.com/sites/US-MI-SB/api/v3/event/{eventID}?format=json"
        )
        return r.json()

    def _create_event(self, j):
        id = j["eventId"]
        name = j["name"]
        date = datetime.fromisoformat(j["startDate"])
        return Event(id, name, date, self.sport, self.league)

    def _create_market(self, j) -> Market:
        # to be implemented by the derived handler.
        raise NotImplementedError()

    def _create_selection(self, j) -> Selection:
        return Selection(
            j["providerOutcomeId"],
            j["label"],
            j["oddsDecimal"],
        )

    def _iterate_events(self, j):
        for event in j["eventGroup"]["events"]:
            yield self._create_event(event)

    def _iterate_markets(self, j):
        for category in j["eventCategories"]:
            for component in category["componentizedOffers"]:
                for offer in chain.from_iterable(component["offers"]):
                    try:
                        yield (offer, self._create_market(offer))
                    except:
                        continue

    def _iterate_selections(self, j):
        for selection in j["outcomes"]:
            yield self._create_selection(selection)
