from datetime import datetime

import requests

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Market import Market
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.util.UserAgents import get_random_user_agent


class Scraper:
    def __init__(
        self,
        sportID,
        competitionID,
        widgetID,
        sport: Sport,
        league: League,
        logger,
    ):
        self.s = self._establish_session()
        self.sportID = sportID
        self.competitionID = competitionID
        self.widgetID = widgetID
        self.sport = sport
        self.league = league

        self.logger = logger

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
        self.logger.debug(f"getting events... {self.sportID}")

        r = self.s.get(
            "https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata",
            params={
                "layoutSize": "Small",
                "page": "CompetitionLobby",
                "sportId": self.sportID,
                "regionId": "9",
                "competitionId": self.competitionID,
                "widgetId": self.widgetID,
                "shouldIncludePayload": "true",
                "compoundCompetitionId": f"1:{self.competitionID}",
                "forceFresh": "1",
            },
        )

        self.logger.debug(f"got events... {r.status_code}")

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
        payload = j["context"] + "|all"
        return Event(id, name, date, self.sport, self.league, payload)

    def _create_market(self, j) -> Market:
        # to be implemented by the derived scraper.
        raise NotImplementedError()

    def _create_selection(self, j) -> Selection:
        return Selection(
            str(j["id"]),
            j["name"]["value"],
            j["price"]["odds"],
        )

    def _iterate_events(self, j):
        try:
            for widget in j["widgets"]:
                for item in widget["payload"]["items"]:
                    for active in item["activeChildren"]:
                        for fixture in active["payload"]["fixtures"]:
                            if fixture["source"] != "V1":
                                self.logger.debug(
                                    f"weird fixture: {fixture['source']}\n{j}"
                                )
                            self.logger.debug("creating event.")
                            yield self._create_event(fixture)
        except Exception as e:
            self.logger.debug(
                f"something went wrong retreiving events: {e}\n{j}"
            )

    def _iterate_markets(self, j):
        for game in j["fixture"]["optionMarkets"]:
            try:
                yield (game, self._create_market(game))
            except Exception:
                continue

    def _iterate_selections(self, j):
        for result in j["options"]:
            yield self._create_selection(result)
