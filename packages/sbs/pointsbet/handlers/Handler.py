import http.client
import json
from datetime import datetime

import requests

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.util.logs import setup_logging


class Handler:
    def __init__(self, competion, sport: Sport, league: League):
        self.competion = competion
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

    def _get(self, host, path):
        conn = http.client.HTTPSConnection(host)
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read()
        # self.logger.debug(response.status)
        # self.logger.debug(data)
        j = json.loads(data.decode())
        conn.close()

        return j

    def _get_events(self):
        return self._get(
            "api.mi.pointsbet.com",
            f"/api/v2/competitions/{self.competion}/events/featured?includeLive=false&page=1",
        )

    def _get_markets(self, eventID):
        self.logger.debug(f"getting market for {eventID}")
        return self._get(
            "api.mi.pointsbet.com", f"/api/mes/v3/events/{eventID}"
        )

    def _create_event(self, j):
        id = j["key"]
        name = j["name"]
        date = datetime.fromisoformat(j["startsAt"])
        return Event(id, name, date, self.sport, self.league)

    def _create_market(self, j) -> Market:
        # to be implemented by the derived handler.
        raise NotImplementedError()

    def _create_selection(self, j) -> Selection:
        return Selection(
            j["fixedMarketId"],
            j["name"],
            j["price"],
        )

    def _iterate_events(self, j):
        for event in j["events"]:
            yield self._create_event(event)

    def _iterate_markets(self, j):
        for market in j["fixedOddsMarkets"]:
            try:
                yield (market, self._create_market(market))
            except:
                continue

    def _iterate_selections(self, j):
        for selection in j["outcomes"]:
            yield self._create_selection(selection)
