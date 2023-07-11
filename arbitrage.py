import sqlite3
from dataclasses import dataclass

conn = sqlite3.connect("database/events.db")
cur = conn.cursor()

res = cur.execute(
    "SELECT events.name, selections.market_id, selections.name,"
    " selections.link, sb_selections.odds, sb_selections.sb FROM events,"
    " selections, sb_selections WHERE events.id = selections.event_id AND"
    " sb_selections.selection_id = selections.id"
)


@dataclass
class Result:
    event: str
    market: str
    selection: str
    link: str
    odds: float
    sb: str

    def __post_init__(self):
        if type(self.odds) is not float:
            self.odds = float(self.odds)
        if type(self.link) is not str:
            self.link = str(self.link)


@dataclass(frozen=True, eq=True)
class Key:
    event: str
    market: str
    link: str

    @classmethod
    def from_result(cls, r: Result):
        return cls(r.event, r.market, r.link)


links = {}
for r in res.fetchall():
    result = Result(*r)
    key = Key.from_result(result)

    if key not in links:
        links[key] = []
    links[key].append(result)


arbs = []
for group in links.values():
    best_odds_for_selection = {}
    event = group[0].event
    market = group[0].market
    for r in group:
        if r.selection not in best_odds_for_selection:
            best_odds_for_selection[r.selection] = r
        elif r.odds > best_odds_for_selection[r.selection].odds:
            best_odds_for_selection[r.selection] = r

    arb = 0.0
    print(event, market)
    for r in best_odds_for_selection.values():
        arb += 1.0 / r.odds
        print(r.sb, r.selection, r.odds)
    arbs.append(arb)
    print(arb)
    if arb < 1:
        print("^^^^ ARB OPPORTUNITY")

    print("\n\n")

arbs.sort()
print(arbs)
