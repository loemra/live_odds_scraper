import re

from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Period import Period
from packages.data.Sport import Sport
from packages.sbs.betmgm.scrapers.Scraper import Scraper


class NFL(Scraper):
    def __init__(self, logger):
        super().__init__(
            11,
            "35",
            "/mobilesports-v1.0/layout/layout_us/"
            "modules/competition/"
            "defaultcontainer-eventsonly-redesign_no_header",
            Sport.FOOTBALL,
            League.NFL,
            logger,
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
                            event = self._create_event(fixture)
                            # these ids are two 'events' that have to do with 
                            # the specific season
                            if event.id in ["14371768", "14274402"]:
                                continue
                            yield event
        except Exception as e:
            self.logger.debug(
                f"something went wrong retreiving events: {e}\n{j}"
            )

    def _create_market(self, j):
        match j["templateCategory"]["id"]:
            case 57 | 738 | 740:
                # spread
                return Market(
                    j["id"],
                    MarketName.SPREAD,
                    Kind.SPREAD,
                    self._get_period(j),
                    *self._get_spread_line(j),
                )
            case 58:
                # moneyline
                return Market(
                    j["id"],
                    MarketName.MONEY_LINE,
                    Kind.H2H,
                )
            case 63 | 737 | 1102:
                # total:
                return Market(
                    j["id"],
                    MarketName.TOTAL,
                    Kind.OVER_UNDER,
                    self._get_period(j),
                    line=self._get_over_under_line(j),
                )

        raise NotImplementedError(
            "Have not implemented this NFL market"
            f" {j['categoryId']} {j['id']} {j['name']['value']}"
        )

    def _get_period(self, j):
        match int(j["parameters"][1]["value"]):
            case 57 | 58 | 53:
                return None
            case 737 | 740:
                return Period.FIRST_QUARTER
            case 738 | 1102:
                return Period.FIRST_HALF

        raise NotImplementedError(
            "Have not implemented period for this NFL market"
            f" {j['categoryId']} {j['id']} {j['name']['value']}"
        )

    def _get_spread_line(self, j):
        m = re.match(
            r"(.*?)\s*(?:\+|\-)?\d+", j["options"][0]["name"]["value"]
        )
        if m is None:
            raise Exception(
                "Unable to get spread line because there is no name match."
            )

        return (m.group(1), int(j["options"][0]["attr"]))

    def _get_over_under_line(self, j):
        return int(j["attr"])
