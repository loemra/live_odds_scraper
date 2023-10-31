from requests import Session

from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Period import Period
from packages.data.Sport import Sport
from packages.sbs.betmgm.handlers.Handler import Handler


class NFL(Handler):
    def __init__(self, s: Session):
        super().__init__(s, 11, "35,211", Sport.FOOTBALL, League.NFL)

    def _create_market(self, j):
        match j["categoryId"]:
            case 57 | 738 | 740:
                # spread
                return Market(
                    j["id"],
                    MarketName.SPREAD,
                    Kind.SPREAD,
                    self._get_period(j),
                    line=self._get_spread_line(j),
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
        match j["categoryId"]:
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
        return int(j["results"][0]["attr"])

    def _get_over_under_line(self, j):
        return int(j["attr"])
