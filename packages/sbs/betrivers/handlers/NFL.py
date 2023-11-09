from requests import Session

from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Selection import Selection
from packages.data.Sport import Sport
from packages.sbs.betrivers.handlers.Handler import Handler


class NFL(Handler):
    def __init__(self):
        super().__init__(1000093656, Sport.FOOTBALL, League.NFL)

    def _create_market(self, j):
        match j["criterion"]["id"]:
            case 1004709447:
                # moneyline
                return Market(j["id"], MarketName.MONEY_LINE, Kind.H2H)

        raise NotImplementedError(
            "Have not implemented this NFL market for betrivers"
            f" {j['criterion']['id']} {j['id']} {j}"
        )

    def _create_selection(self, j) -> Selection:
        if j["oddsFractional"] == "Evens":
            odds = 2
        else:
            a, b = j["oddsFractional"].split("/")
            odds = 1 + int(a) / int(b)

        return Selection(
            j["id"],
            j["participant"],
            odds,
        )
