from database.events_database import clear_db
from database.translaters.translater import reset_translaters

print("confirm: ")
res = input()

if res != "yes":
    exit()

clear_db()
reset_translaters()
