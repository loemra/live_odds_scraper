import os

print("confirm: ")
res = input()

if res != "yes":
    exit()

with open("database/events.db", "w") as f:
    f.write("")

# run initial setup code for the db.
from database import setup_db

for path in os.listdir("logs"):
    with open(f"logs/{path}", "w") as f:
        f.write("")
