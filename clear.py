import shutil

from database import setup_db


def run():
    print("confirm: ")
    res = input()

    if res != "yes":
        exit()

    with open("database/events.db", "w") as f:
        f.write("")

    # run initial setup code for the db.
    setup_db.run()

    shutil.rmtree("logs")


if __name__ == "__main__":
    run()
