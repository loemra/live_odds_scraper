from datetime import datetime

import requests

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.util.UserAgents import get_random_user_agent


class Scraper:
    def __init__(self, sportID, competitionIDs, sport: Sport, league: League):
        self.s = self._establish_session()
        self.sportID = sportID
        self.competitionIDs = competitionIDs
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

    def _establish_session(self):
        s = requests.Session()
        s.headers = {
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "sports.mi.betmgm.com",
            "Origin": "null",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": get_random_user_agent(),
        }
        s.get("https://sports.mi.betmgm.com/")

        return s

    def _get_events(self):
        r = self.s.post(
            "https://sports.mi.betmgm.com/cds-api/"
            "random-multi-generator/random-events",
            params={
                "x-bwin-accessid": (
                    "NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh"
                ),
                "lang": "en-us",
                "country": "US",
                "userCountry": "US",
                "subdivision": "US-Michigan",
            },
            json={
                "sportId": self.sportID,
                "minOdds": 1.01,
                "maxOdds": 10,
                "gridGroupId": "c6jgebjaf",
                "competitionIds": self.competitionIDs,
            },
        )

        return r.json()

    def _get_markets(self, eventID):
        r = self.s.get(
            "https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view",
            params={
                "x-bwin-accessid": (
                    "NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh"
                ),
                "lang": "en-us",
                "country": "US",
                "userCountry": "US",
                "subdivision": "US-Michigan",
                "offerMapping": "All",
                "scoreboardMode": "Full",
                "fixtureIds": eventID,
                "state": "Latest",
                "includePrecreatedBetBuilder": "true",
                "supportVirtual": "false",
                "useRegionalisedConfiguration": "true",
                "includeRelatedFixtures": "true",
                "statisticsModes": "All",
            },
        )

        return r.json()

    def _create_event(self, j):
        id = j["id"]
        name = j["name"]["value"]
        date = datetime.fromisoformat(j["startDate"])
        return Event(id, name, date, self.sport, self.league)

    def _create_market(self, _) -> Market:
        # to be implemented by the derived scraper.
        raise NotImplementedError()

    def _create_selection(self, j) -> Selection:
        return Selection(
            str(j["id"]),
            j["name"]["value"],
            j["price"]["odds"],
        )

    def _iterate_events(self, j):
        for fixture in j["fixtures"]:
            yield self._create_event(fixture)

    def _iterate_markets(self, j):
        for game in j["fixture"]["optionMarkets"]:
            try:
                yield (game, self._create_market(game))
            except Exception:
                continue

    def _iterate_selections(self, j):
        for result in j["options"]:
            yield self._create_selection(result)
