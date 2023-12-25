from packages.sbs.betmgm.scrapers.scraper import Scraper


class NBA(Scraper):
    def __init__(self, logger):
        payload = (
            "https://sports.mi.betmgm.com/en/sports/api/widget",
            7,
            "6004",
            (
                "/mobilesports-v1.0/layout/layout_us/pages/"
                "competitionlobby/redesign-nba"
            ),
        )
        super().__init__(payload, logger)

    def _iterate_events(self, j):
        try:
            for widget in j["widgets"]:
                for pod in widget["payload"]["pods"].values():
                    for fixture in pod["fixtures"]:
                        self._logger.debug("creating event.")
                        yield self._create_event(fixture)
                    break
        except Exception as e:
            self._logger.debug(
                f"something went wrong iterating events: {e}\n{j}"
            )

    def _create_market(self, j):
        match j["templateCategory"]["id"]:
            case 43:
                # moneyline
                return {
                    "id": j["id"],
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
            except Exception:
                continue

    def _iterate_selections(self, j):
        for result in j["results"]:
            yield self._create_selection(result)

    def _create_selection(self, j):
        return {
            "id": str(j["id"]),
            "name": j["name"]["value"],
            "odds": j["odds"],
        }
