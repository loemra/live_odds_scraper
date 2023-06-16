from dataclasses import dataclass

@dataclass
class Sportsbook:
    name: str

    def update_odds(msg):
        print(msg)