from packages.sbs.betmgm.scrapers.scraper import Scraper


class NBA(Scraper):
    def __init__(self, sb, logger):
        payload = (
            "https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata",
            7,
            "6004",
            (
                "/mobilesports-v1.0/layout/layout_us/modules/basketball/"
                "nba/nba-gamelines-complobby"
            ),
        )
        super().__init__(sb, "NBA", payload, logger)

    def _create_market(self, j):
        match j["templateCategory"]["id"]:
            case 43:
                # moneyline
                return {
                    "name": "money_line",
                    "kind": "h2h",
                }

        raise NotImplementedError(
            "Have not implemented this NBA market"
            f" {j['templateCategory']['id']}\n{j}"
        )

    def _iterate_markets(self, j):
        for game in j["fixture"]["games"]:
            try:
                yield (game, self._create_market(game))
            except NotImplementedError:
                pass
            except Exception as e:
                self._logger.warning(
                    f"something went wrong iterating markets: {e}\n{game}"
                )

    def _iterate_selections(self, j):
        for result in j["results"]:
            yield self._create_selection(result)

    def _create_selection(self, j):
        return {
            "id": str(j["id"]),
            "name": j["name"]["value"],
            "odds": j["odds"],
        }
