import asyncio
from datetime import datetime

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential


class Scraper:
    def __init__(self, sb, league, payload, logger):
        self._sb = sb
        self._league = league
        self._payload = payload
        self._logger = logger

    def __repr__(self) -> str:
        return self._league

    async def yield_events(self):
        async for event in self._session_wrapper(self._yield_events):
            yield event

    async def _yield_events(self, session):
        events = await self._get_events(session)
        for event in asyncio.as_completed([
            self._process_event(session, e)
            for e in self._iterate_events(events)
        ]):
            yield await event

    async def _process_event(self, session, event):
        self._logger.info(f"processing event {event['id']} {event['name']}")
        markets = await self._get_markets(session, event["id"])
        event["markets"] = []
        for j, market in self._iterate_markets(markets):
            market["selections"] = list(self._iterate_selections(j))
            event["markets"].append(market)
        return event

    def _iterate_events(self, j):
        try:
            for widget in j["widgets"]:
                for item in widget["payload"]["items"]:
                    for active in item["activeChildren"]:
                        for fixture in active["payload"]["fixtures"]:
                            yield self._create_event(fixture)
        except Exception as e:
            self._logger.warning(
                f"something went wrong iterating events: {e}\n{j}"
            )

    def _iterate_markets(self, j):
        for game in j["fixture"]["optionMarkets"]:
            try:
                yield (game, self._create_market(game))
            except NotImplementedError:
                pass
            except Exception as e:
                self._logger.warning(
                    f"something went wrong iterating markets: {e}\n{game}"
                )

    def _iterate_selections(self, j):
        for result in j["options"]:
            yield self._create_selection(result)

    def _create_event(self, j):
        return {
            "id": str(j["id"]),
            "sb": self._sb,
            "name": j["name"]["value"],
            "league": self._league,
            "date": datetime.fromisoformat(j["startDate"]),
            "payload": j["context"] + "|all",
        }

    def _create_market(self, j):
        raise NotImplementedError

    def _create_selection(self, j):
        return {
            "id": str(j["id"]),
            "name": j["name"]["value"],
            "odds": j["price"]["odds"],
        }

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=5, max=30))
    async def _get_events(self, session):
        url, sport_id, competition_id, widget_id = self._payload
        self._logger.debug("getting events...")
        async with session.get(
            url,
            params={
                "layoutSize": "Small",
                "page": "CompetitionLobby",
                "sportId": sport_id,
                "regionId": "9",
                "competitionId": competition_id,
                "widgetId": widget_id,
                "shouldIncludePayload": "true",
                "compoundCompetitionId": f"1:{competition_id}",
                "forceFresh": "1",
            },
        ) as resp:
            self._logger.info(f"get events status: {resp.status}")
            return await resp.json()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=5, max=30))
    async def _get_markets(self, session, event_id):
        self._logger.debug(f"getting markets for {event_id}...")
        async with session.get(
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
                "fixtureIds": event_id,
                "state": "Latest",
                "includePrecreatedBetBuilder": "true",
                "supportVirtual": "false",
                "useRegionalisedConfiguration": "true",
                "includeRelatedFixtures": "true",
                "statisticsModes": "All",
            },
        ) as resp:
            self._logger.info(f"get market {event_id} status: {resp.status}")
            return await resp.json()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=5, max=30))
    async def _session_wrapper(self, async_generator_callback):
        headers = {
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
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0"
                " Safari/537.36"
            ),
        }

        self._logger.debug("establishing session...")
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get("https://sports.mi.betmgm.com/") as resp:
                self._logger.info(f"establish session status: {resp.status}")
            async for r in async_generator_callback(session):
                yield r
