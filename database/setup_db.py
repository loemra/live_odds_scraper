import sqlite3

conn = sqlite3.connect("database/events.db")
cur = conn.cursor()


def _maybe_create_events():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events(name TEXT, sport TEXT, date INTEGER)"
    )


def _maybe_create_markets():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS markets(name TEXT, kind TEXT, period TEXT,"
        " player TEXT, line REAL, event_id, FOREIGN KEY(event_id) REFERENCES"
        " events(rowid))"
    )


def _maybe_create_selections():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS selections(name TEXT, market_id, FOREIGN"
        " KEY (market_id) REFERENCES markets(rowid))"
    )


def _maybe_create_sb_events():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_events(id TEXT, sb TEXT, name TEXT, url"
        " TEXT, event_id, FOREIGN KEY(event_id) REFERENCES events(rowid),"
        " PRIMARY KEY(id, sb)) WITHOUT ROWID"
    )


def _maybe_create_sb_markets():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_markets(id TEXT, sb TEXT, player TEXT,"
        " market_id, FOREIGN KEY (market_id) REFERENCES markets(rowid), PRIMARY"
        " KEY(id, sb)) WITHOUT ROWID"
    )


def _maybe_create_sb_selections():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_selections(id TEXT, sb TEXT, odds REAL,"
        " selection_id, FOREIGN KEY(selection_id) REFERENCES selections(rowid),"
        " PRIMARY KEY(id, sb))"
    )


def _maybe_create_history():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS history(odds REAL, date INTEGER,"
        " sb_selection_id, FOREIGN KEY (sb_selection_id) REFERENCES"
        " sb_selections(rowid))"
    )


def run():
    _maybe_create_events()
    _maybe_create_markets()
    _maybe_create_selections()
    _maybe_create_sb_events()
    _maybe_create_sb_markets()
    _maybe_create_sb_selections()
    _maybe_create_history()

    conn.commit()


if __name__ == "__main__":
    run()
'''
_maybe_add_sbs(["fox_bets", "bovada"])
_maybe_add_sports(["soccer", "tennis"])
_maybe_add_sb_sports(
    [
        ("SOCCER", "soccer", "fox_bets"),
        ("SOCC", "soccer", "bovada"),
        ("TENN", "tennis", "bovada"),
    ]
)
_maybe_add_markets(
    [
        ("soccer_game_result", "TEAM_NAME"),
        ("soccer_over_under_total_goals", "OVER_UNDER"),
        ("soccer_both_teams_to_score", "YES_NO"),
        ("tennis_spread", "SPREAD"),
        ("tennis_game_result", "TEAM_NAME"),
        ("tennis_over_under_total_games", "OVER_UNDER"),
    ]
)

# TODO: instead of just sportsbook id this will be the sportsbook payload.
# TODO: possibly have multiple primary keys: name & period
""" FOX_BETS
('SOCCER:FT:AXB', 'full', 'soccer_game_result', 'fox_bets')
('SOCCER:FT:BTS', 'full', 'soccer_both_teams_to_score', 'fox_bets')
('SOCCER:FT:OU', 'full', 'soccer_over_under_total_goals', 'fox_bets')
('SOCCER:P:BTS', 'H1', 'soccer_both_teams_to_score', 'fox_bets')
('SOCCER:P:BTS', 'H2', 'soccer_both_teams_to_score', 'fox_bets')
('SOCCER:P:OU', 'H1', 'soccer_over_under_total_goals', 'fox_bets')
('SOCCER:P:OU', 'H2', 'soccer_over_under_total_goals', 'fox_bets')
"""

""" BOVADA
Market(name='1', period='First Half', kind=<MarketKind.TEAM_NAME: 1>)
Market(name='1', period='Regulation Time', kind=<MarketKind.TEAM_NAME: 1>)
Market(name='120755', period='1st Set', kind=<MarketKind.OVER_UNDER: 2>)
Market(name='120755', period='Match', kind=<MarketKind.OVER_UNDER: 2>)
Market(name='13', period='First Half', kind=<MarketKind.OVER_UNDER: 2>)
Market(name='13', period='Regulation Time', kind=<MarketKind.OVER_UNDER: 2>)
Market(name='350', period='First Half', kind=<MarketKind.YES_NO: 3>)
Market(name='350', period='Regulation Time', kind=<MarketKind.YES_NO: 3>)
Market(name='67', period='1st Set', kind=<MarketKind.SPREAD: 4>)
Market(name='67', period='Match', kind=<MarketKind.SPREAD: 4>)
Market(name='68', period='1st Set', kind=<MarketKind.TEAM_NAME: 1>)
Market(name='68', period='2nd Set', kind=<MarketKind.TEAM_NAME: 1>)
Market(name='68', period='Match', kind=<MarketKind.TEAM_NAME: 1>)
"""

_maybe_add_sb_markets(
    [
        ("SOCCER:FT:AXB", "full", "soccer_game_result", "fox_bets"),
        ("SOCCER:FT:BTS", "full", "soccer_both_teams_to_score", "fox_bets"),
        ("SOCCER:FT:OU", "full", "soccer_over_under_total_goals", "fox_bets"),
        ("SOCCER:P:BTS", "H1", "soccer_both_teams_to_score", "fox_bets"),
        ("SOCCER:P:BTS", "H2", "soccer_both_teams_to_score", "fox_bets"),
        ("SOCCER:P:OU", "H1", "soccer_over_under_total_goals", "fox_bets"),
        ("SOCCER:P:OU", "H2", "soccer_over_under_total_goals", "fox_bets"),
        ("1", "soccer_game_result", "bovada"),
        ("13", "soccer_over_under_total_goals", "bovada"),
        ("350", "soccer_both_teams_to_score", "bovada"),
        ("67", "tennis_spread", "bovada"),
        ("68", "tennis_game_result", "bovada"),
        ("120755", "tennis_over_under_total_games", "bovada"),
    ]
)


conn.commit()
conn.close()
'''
