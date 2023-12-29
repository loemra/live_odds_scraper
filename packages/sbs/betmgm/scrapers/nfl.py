from packages.sbs.betmgm.scrapers.scraper import Scraper


class NFL(Scraper):
    def __init__(self, sb, logger):
        payload = (
            "https://sports.mi.betmgm.com/en/sports/api/widget/widgetdata",
            11,
            "35",
            (
                "/mobilesports-v1.0/layout/layout_us/"
                "modules/competition/"
                "defaultcontainer-eventsonly-redesign_no_header"
            ),
        )
        super().__init__(sb, "NFL", payload, logger)

    def _create_market(self, j):
        match j["templateCategory"]["id"]:
            case 58:
                # moneyline
                return {
                    "name": "money_line",
                    "kind": "h2h",
                }

        raise NotImplementedError(
            "Have not implemented this NFL market"
            f" {j['templateCategory']['id']}\n{j}"
        )
