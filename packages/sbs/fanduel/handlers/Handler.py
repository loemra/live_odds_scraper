import functools
import json
import re
from datetime import datetime
from threading import Event as ThreadingEvent
from threading import Thread
from time import sleep

import seleniumwire.undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from packages.data.Event import Event
from packages.data.League import League
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.util.logs import setup_logging


class Handler:
    def __init__(
        self, events_url, market_url, tabs, sport: Sport, league: League
    ):
        self.events_url = events_url
        self.market_url = market_url
        self.tabs = tabs
        self.sport = sport
        self.league = league

        options = Options()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        self.driver = uc.Chrome(
            options=options,
            seleniumwire_options={
                "disable_encoding": True,
                "request_storage_max_size": 10,
            },
        )

        self.grabbed_events = ThreadingEvent()
        self.grabbed_markets = ThreadingEvent()

        self.logger = setup_logging(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.quit()

    def _blocker(self, request):
        stack = [
            "https://sportsbook.fanduel.com/",
            "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page",
            "https://sbapi.mi.sportsbook.fanduel.com/api/event-page",
        ]
        if True not in [
            bool(re.match(s, request.url)) for s in stack
        ] and not request.path.endswith(".js"):
            request.abort()

    def _event_interceptor(self, request, response):
        if re.match(
            "https://sbapi.mi.sportsbook.fanduel.com/api/content-managed-page",
            request.url,
        ):
            self.events = json.loads(response.body.decode())
            self.grabbed_events.set()
            sleep(0.0001)

    def _market_interceptor(self, tab, request, response):
        if self.grabbed_markets.is_set():
            return

        if (
            re.match(
                "https://sbapi.mi.sportsbook.fanduel.com/api/event-page",
                request.url,
            )
            and tab in request.url
        ):
            try:
                self.logger.debug(request.url)
                self.markets = json.loads(response.body.decode())
            except:
                self.markets = None
            self.grabbed_markets.set()
            sleep(0.0001)

    def yield_events(self):
        self.driver.request_interceptor = self._blocker
        self.driver.response_interceptor = self._event_interceptor

        self._get_events(self.events_url)
        self.grabbed_events.wait()

        for event in self._iterate_events(self.events):
            if event.id < 29000000 or event.id == 30327496:
                continue

            self.logger.debug(f"event {event.name}")

            for tab in self.tabs:
                self.driver.response_interceptor = functools.partial(
                    self._market_interceptor, tab
                )

                self.grabbed_markets.clear()
                self._get_markets(
                    f"{self.market_url}{event.name.replace(' ', '-').lower()}-{event.id}?tab={tab}"
                )
                self.grabbed_markets.wait(timeout=5)

                if self.markets is None:
                    print(f"SOMETHING WENT WRONG... {event.id} {tab}")
                    continue

                event.markets.extend(
                    [market for market in self._iterate_markets(self.markets)]
                )

                sleep(1)

            for market in event.markets:
                self.logger.debug(market)

            yield event
            sleep(5)

    def _get_events(self, url):
        # Thread(target=self.driver.get, args=(url,), daemon=True).start()
        self.driver.get(url)

    def _get_markets(self, url):
        self.driver.get(url)
        # Thread(target=self.driver.get, args=(url,), daemon=True).start()

    def _create_event(self, j):
        id = j["eventId"]
        name = j["name"]
        date = datetime.fromisoformat(j["openDate"])
        return Event(id, name, date, self.sport, self.league)

    def _create_markets(self, j):
        raise NotImplementedError()

    def _create_selection(self, j, market_id) -> Selection:
        return Selection(
            f'{str(market_id)}:{str(j["selectionId"])}',
            j["runnerName"],
            j["winRunnerOdds"]["trueOdds"]["decimalOdds"]["decimalOdds"],
        )

    def _iterate_events(self, j):
        for event in j["attachments"]["events"].values():
            yield self._create_event(event)

    def _iterate_markets(self, j):
        for m in j["attachments"]["markets"].values():
            for market in self._create_markets(m):
                yield market

    def _iterate_selections(self, j):
        for selection in j["runners"]:
            yield (selection, self._create_selection(selection, j["marketId"]))
