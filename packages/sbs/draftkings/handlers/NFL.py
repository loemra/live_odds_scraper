from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Sport import Sport
from packages.sbs.draftkings.handlers.Handler import Handler


class NFL(Handler):
    def __init__(self):
        super().__init__(88808, Sport.FOOTBALL, League.NFL)

    def _create_market(self, j):
        match j["label"]:
            case "Moneyline":
                return Market(
                    j["providerOfferId"], MarketName.MONEY_LINE, Kind.H2H
                )
        raise NotImplementedError(f"Have not implemented this NFL market {j}")
