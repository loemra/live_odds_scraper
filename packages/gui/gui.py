import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
from threading import Lock


class GUI:
    def __init__(self, db):
        self.db = db
        self.data = None
        self.lock = Lock()

    def run(self):
        self.db.subscribe_to_updates(self._update)

        def to_be_wrapped(stdscr):
            win = curses.newwin(3, 78, 2, 2)
            box = Textbox(win)

            while True:
                # get search keys...
                search = box.gather().strip().replace("\n", "")

                with self.lock:
                    filtered = self._filter(self.data, search)

                self._draw(
                    stdscr,
                    box,
                    self._stringify(filtered),
                )

        wrapper(to_be_wrapped)

    def _filter(self, data, search):
        if search == "":
            return

        filtered = []
        for i in data:
            for k, v in i.items():
                if search.lower() in k.lower() or (
                    isinstance(v, str) and search.lower() in v.lower()
                ):
                    filtered.append(i)
        return filtered

    def _stringify(self, data):
        s = ""
        for i in data:
            s += (
                f"{i['name']}".center(40)
                + "|"
                + f"{i['market']}".center(15)
                + "\n"
                + "|".join([
                    f"{s['team']}: {s['decimal']} ({s['american']:+})".center(
                        25
                    )
                    for s in i["selections"]
                ])
                + "-" * 56
            )
        return s

    def _draw(self, stdscr, box, text):
        stdscr.clear()
        rectangle(stdscr, 1, 1, 5, 80)

        stdscr.addstr(10, 1, text)

        stdscr.refresh()
        box.edit()

    def _update(self):
        with self.lock:
            self.data = self.db.snapshot()
