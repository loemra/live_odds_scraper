import json
import sqlite3

with open("secrets.json", "r") as f:
    secrets = json.load(f)

con = sqlite3.connect(secrets["db-name"])
cur = con.cursor()

cur.executescript("""
    BEGIN;

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        date INTEGER NOT NULL,
        sport TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sb_events (
        id TEXT NOT NULL,
        sb TEXT NOT NULL,
        name TEXT NOT NULL,
        event_id INTEGER NOT NULL,
        PRIMARY KEY (id, sb),
        FOREIGN KEY (event_id) REFERENCES events (id)
    );

    CREATE TABLE IF NOT EXISTS markets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        period TEXT,
        participant TEXT,
        line REAL,
        event_id INTEGER NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events (id)
    );

    CREATE TABLE IF NOT EXISTS sb_markets (
        id TEXT NOT NULL,
        sb TEXT NOT NULL,
        market_id INTEGER NOT NULL,
        PRIMARY KEY (id, sb),
        FOREIGN KEY (market_id) REFERENCES markets (id)
    );

    CREATE TABLE IF NOT EXISTS selections (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        market_id INTEGER NOT NULL,
        FOREIGN KEY (market_id) REFERENCES markets (id)
    );

    
    CREATE TABLE IF NOT EXISTS sb_selections (
        id TEXT NOT NULL,
        sb TEXT NOT NULL,
        odds REAL,
        selection_id INTEGER NOT NULL,
        PRIMARY KEY (id, sb),
        FOREIGN KEY (selection_id) REFERENCES selections (id)
    );

    COMMIT;
""")
