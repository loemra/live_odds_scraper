import json
import sqlite3
import sys

if __name__ == "__main__":
    with open("secrets.json", "r") as f:
        secrets = json.load(f)

    if len(sys.argv) == 1:
        con = sqlite3.connect(secrets["db-name"])
    else:
        con = sqlite3.connect(secrets[sys.argv[1]])
        con.executescript("""
            BEGIN;
            DROP TABLE events;
            DROP TABLE sb_events;
            DROP TABLE markets;
            DROP TABLE selections;
            DROP TABLE sb_selections;
            DROP TABLE odds_history;
            DROP TABLE matches;
            COMMIT;
        """)

    con.executescript("""
        BEGIN;

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            date INTEGER NOT NULL,
            sport TEXT NOT NULL,
            league TEXT NOT NULL,
            UNIQUE (name, date, sport, league)
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
            FOREIGN KEY (event_id) REFERENCES events (id),
            UNIQUE (name, kind, period, participant, line, event_id)
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

        CREATE TABLE IF NOT EXISTS odds_history (
            id TEXT NOT NULL,
            sb TEXT NOT NULL,
            odds REAL NOT NULL,
            date REAL NOT NULL,
            FOREIGN KEY (id, sb) REFERENCES sb_selections (id, sb)
        );

        CREATE TABLE IF NOT EXISTS matches (
            match TEXT NOT NULL,
            potential TEXT NOT NULL,
            result INTEGER NOT NULL,
            CHECK (result IN (0, 1)),
            UNIQUE (match, potential, result)
        );

        COMMIT;
    """)
