import http.client
import json
from datetime import datetime

from requests import Session

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.data.Sport import Sport


class Handler:
    def __init__(self, groupId, sport: Sport, league: League):
        self.groupId = groupId
        self.sport = sport
        self.league = league

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
        j = json.loads(response.read().decode())
        conn.close()

        return j

    def _get_events(self):
        total_pages = 2
        page = 1
        events = []
        while page <= total_pages:
            j = self._get(
                "mi.betrivers.com",
                f"/api/service/sportsbook/offering/listview/events?t=2023109320&cageCode=910&type=live&type=prematch&groupId={self.groupId}&pageNr={page}&pageSize=10&offset=0",
            )

            total_pages = j["paging"]["totalPages"]
            page += 1
            events.extend(j["items"])

        return events

    def _get_markets(self, eventID):
        return self._get(
            "eu-offering-api.kambicdn.com",
            f"/offering/v2018/rsiusmi/betoffer/event/{eventID}.json",
        )

    def _create_event(self, j):
        id = j["id"]
        name = j["name"]
        date = datetime.fromisoformat(j["start"])
        return Event(id, name, date, self.sport, self.league)

    def _create_market(self, j) -> Market:
        # to be implemented by the derived handler.
        raise NotImplementedError()

    def _create_selection(self, j) -> Selection:
        if j["oddsFractional"] == "Evens":
            odds = 2
        else:
            a, b = j["oddsFractional"].split("/")
            odds = 1 + int(a) / int(b)

        return Selection(
            j["id"],
            j["label"],
            odds,
        )

    def _iterate_events(self, j):
        for event in j:
            yield self._create_event(event)

    def _iterate_markets(self, j):
        for market in j["betOffers"]:
            try:
                yield (market, self._create_market(market))
            except:
                continue

    def _iterate_selections(self, j):
        for result in j["outcomes"]:
            yield self._create_selection(result)
