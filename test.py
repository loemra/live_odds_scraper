# import db2.setup_db

import sqlite3

conn = sqlite3.connect("db2/events.db")
cur = conn.cursor()

res = cur.execute("SELECT * FROM events")
print(res.fetchall())
