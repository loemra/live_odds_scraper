from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.sbs.betmgm.scrapers.Scraper import Scraper


class NBA(Scraper):
    def __init__(self, logger):
        super().__init__(
            7,
            "6004",
            "/mobilesports-v1.0/layout/layout_us/"
            "modules/basketball/nba/nba-gamelines-complobby",
            Sport.BASKETBALL,
            League.NBA,
            logger,
        )

    def _create_market(self, j):
        match j["templateCategory"]["id"]:
            case 43:
                # moneyline
                return Market(
                    j["id"],
                    MarketName.MONEY_LINE,
                    Kind.H2H,
                )

        raise NotImplementedError(
            "Have not implemented this NBA market"
            f" {j['categoryId']} {j['id']} {j['name']['value']}"
        )

    def _iterate_markets(self, j):
        for game in j["fixture"]["games"]:
            try:
                yield (game, self._create_market(game))
            except Exception:
                continue

    def _iterate_selections(self, j):
        for result in j["results"]:
            yield self._create_selection(result)

    def _create_selection(self, j) -> Selection:
        return Selection(
            str(j["id"]),
            j["name"]["value"],
            j["odds"],
        )


