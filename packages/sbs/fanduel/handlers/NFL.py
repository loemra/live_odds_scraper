from packages.data.Kind import Kind
from packages.data.League import League
from packages.data.Market import Market
from packages.data.MarketName import MarketName
from packages.data.Period import Period
from packages.data.Sport import Sport
from packages.sbs.fanduel.handlers.Handler import Handler


class NFL(Handler):
    def __init__(self):
        super().__init__(
            "https://sportsbook.fanduel.com/navigation/nfl",
            "https://sportsbook.fanduel.com/football/nfl/",
            ["popular", "1st-quarter", "1st-half", "totals"],
            Sport.FOOTBALL,
            League.NFL,
        )

    def _create_markets(self, j):
        match j["marketType"]:
            case "MONEY_LINE":
                yield Market(
                    j["marketId"],
                    MarketName.MONEY_LINE,
                    Kind.H2H,
                    selection=[s for _, s in self._iterate_selections(j)],
                )
            case "MATCH_HANDICAP_(2-WAY)" | "1ST_QUARTER_HANDICAP" | "FIRST_HALF_HANDICAP":
                yield Market(
                    j["marketId"],
                    MarketName.SPREAD,
                    Kind.SPREAD,
                    self._get_period(j["marketType"]),
                    *self._get_spread_attributes(j),
                )
            case "ALTERNATE_HANDICAP":
                self.logger.debug("Getting alternate handicap")
                for a in self._group_alternate_spreads(j):
                    self.logger.debug(a)
                    yield Market(
                        j["marketId"],
                        MarketName.SPREAD,
                        Kind.SPREAD,
                        None,
                        *a,
                    )
            case "":
                pass

    def _get_period(self, marketType):
        match marketType:
            case "MATCH_HANDICAP_(2-WAY)":
                return None
            case "1ST_QUARTER_HANDICAP":
                return Period.FIRST_QUARTER
            case "FIRST_HALF_HANDICAP":
                return Period.FIRST_HALF

        raise NotImplementedError(
            f"Have not implemented period for this NFL market {marketType}"
        )

    def _get_spread_attributes(self, j):
        line = None
        participant = None
        selections = []
        for s, selection in self._iterate_selections(j):
            n = selection.name
            if s["result"]["type"] == "HOME":
                line = s["handicap"]
                participant = n
            selections.append(selection)

        if line is None or participant is None or len(selections) != 2:
            raise Exception(
                f"Something went wrong when trying to create spread. {j}"
            )

        return (participant, line, selections)

    def _group_alternate_spreads(self, j):
        groups = {}
        for s, selection in self._iterate_selections(j):
            n = selection.name
            line = float(n[n.find("(") + 1 : n.find(")")])
            unified_line = line * (1 if s["result"]["type"] == "HOME" else -1)
            if unified_line not in groups:
                groups[unified_line] = {"selections": []}
            groups[unified_line]["selections"].append(selection)
            if line > 0:
                participant = n[: n.find("(")].strip()
                groups[unified_line]["participant"] = participant

        self.logger.debug(groups)
        return [
            (v["participant"], abs(k), v["selections"])
            for k, v in groups.items()
            if v["participant"] is not None
            and k is not None
            and len(v["selections"]) == 2
        ]
