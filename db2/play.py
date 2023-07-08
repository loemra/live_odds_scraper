import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()


def _maybe_create_events_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, name TEXT,"
        " sport TEXT, date INTEGER, url TEXT) WITHOUT ROWID"
    )


def _maybe_create_markets_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS markets(id TEXT PRIMARY KEY, kind TEXT)"
        " WITHOUT ROWID"
    )


def _maybe_create_events_markets_relationship_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS events_markets_relationships(event_id TEXT"
        " FOREIGN KEY, market_id TEXT FOREIGN KEY)"
    )


def _maybe_create_selections_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS selections(id TEXT PRIMARY KEY, name TEXT)"
        " WITHOUT ROWID"
    )


def _maybe_create_markets_selections_relationship_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS markets_selections_relationships(market_id"
        " TEXT FOREIGN KEY, selection_id TEXT FOREIGN KEY)"
    )


def _maybe_create_sportsbook_odds_table():
    cur.execute(
        "CREATE TABLE IF NOT EXISTS sportsbook_odds(id TEXT PRIMARY KEY, name"
        " TEXT) WITHOUT ROWID"
    )


conn.close()
