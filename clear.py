from database.events_database import clear_db
from database.translaters.translater import reset_translaters

print("confirm: ")
res = input()

if res != "yes":
    exit()

clear_db()
reset_translaters()

with open("logs/events_database.log", "w") as f:
    f.write("")

with open("logs/events_updater.log", "w") as f:
    f.write("")

with open("logs/fox_bets.log", "w") as f:
    f.write("")

with open("logs/bovada.log", "w") as f:
    f.write("")
