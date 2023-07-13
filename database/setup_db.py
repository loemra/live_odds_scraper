import sqlite3
from typing import Tuple

conn = sqlite3.connect("database/events.db")
cur = conn.cursor()


def _maybe_create_events():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, name TEXT,"
        " sport TEXT, date INTEGER)"
    )


def _maybe_create_sports():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sports(name TEXT PRIMARY KEY) WITHOUT ROWID"
    )


def _maybe_create_markets():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS markets(name TEXT PRIMARY KEY, kind TEXT),"
        " WITHOUT ROWID"
    )


def _maybe_create_selections():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS selections(id INTEGER PRIMARY KEY, name"
        " TEXT, link TEXT, event_id, market_id, FOREIGN KEY (event_id)"
        " REFERENCES events(id), FOREIGN KEY (market_id) REFERENCES"
        " markets(name))"
    )


def _mabye_create_sbs():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sbs(name TEXT PRIMARY KEY) WITHOUT ROWID"
    )


def _maybe_create_sb_events():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_events(id TEXT, url TEXT, name TEXT,"
        " event_id, sb, FOREIGN KEY (event_id) REFERENCES events(id), FOREIGN"
        " KEY (sb) REFERENCES sbs(name))"
    )


def _maybe_create_sb_sports():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_sports(name, sport, sb, FOREIGN KEY"
        " (sport) REFERENCES sports(name), FOREIGN KEY (sb) REFERENCES"
        " sbs(name))"
    )


def _maybe_create_sb_markets():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_markets(name TEXT PRIMARY KEY,"
        " market_id, sb, FOREIGN KEY (market_id) REFERENCES markets(name),"
        " FOREIGN KEY (sb) REFERENCES sbs(name)) WITHOUT ROWID"
    )


def _maybe_create_sb_selections():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sb_selections(id TEXT, odds TEXT, name"
        " TEXT, selection_id, sb, FOREIGN KEY (selection_id) REFERENCES"
        " selections(id), FOREIGN KEY (sb) REFERENCES sbs(name))"
    )


def _maybe_create_history():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS history(odds TEXT, time INTEGER,"
        " sb_selection_id, FOREIGN KEY (sb_selection_id) REFERENCES"
        " sb_selections(rowid))"
    )


_maybe_create_events()
_maybe_create_sports()
_maybe_create_markets()
_maybe_create_selections()
_mabye_create_sbs()
_maybe_create_sb_events()
_maybe_create_sb_sports()
_maybe_create_sb_markets()
_maybe_create_sb_selections()
_maybe_create_history()

conn.commit()


def _maybe_add_sbs(sbs: list[str]):
    cur.executemany("INSERT INTO sbs VALUES (?)", [(sb,) for sb in sbs])


def _maybe_add_sports(sports: list[str]):
    cur.executemany(
        "INSERT INTO sports VALUES (?)",
        [(sport,) for sport in sports],
    )


def _maybe_add_sb_sports(sb_sports: list[Tuple]):
    cur.executemany(
        "INSERT INTO sb_sports VALUES (?, ?, ?)",
        sb_sports,
    )


def _maybe_add_markets(markets: list[Tuple]):
    cur.executemany("INSERT INTO markets VALUES (?, ?)", markets)


def _maybe_add_sb_markets(sb_markets: list[Tuple]):
    cur.executemany(
        "INSERT INTO sb_markets VALUES (?, ?, ?)",
        sb_markets,
    )


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
_maybe_add_sb_markets(
    [
        ("SOCCER:FT:AXB", "soccer_game_result", "fox_bets"),
        ("SOCCER:FT:OU", "soccer_over_under_total_goals", "fox_bets"),
        ("SOCCER:FT:BTS", "soccer_both_teams_to_score", "fox_bets"),
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
