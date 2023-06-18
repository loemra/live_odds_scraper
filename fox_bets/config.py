import json


def get_config():
    with open("fox_bets/config.json", "r") as f:
        j = json.load(f)
    return j


config = get_config()


def get_odds(ri) -> float:
    return float(config["odds"][ri]["decimal"])
