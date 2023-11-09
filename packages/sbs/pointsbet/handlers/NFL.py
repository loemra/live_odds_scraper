from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Period import Period
from packages.data.Sport import Sport
from packages.sbs.pointsbet.handlers.Handler import Handler


class NFL(Handler):
    def __init__(self):
        super().__init__(2, Sport.FOOTBALL, League.NFL)

    def _create_market(self, j):
        match j["eventClass"]:
            case "Moneyline":
                return Market(j["key"], MarketName.MONEY_LINE, Kind.H2H)

        raise NotImplementedError(
            "Have not implemented this NFL market"
            f" {j['categoryId']} {j['id']} {j['name']['value']}"
        )
