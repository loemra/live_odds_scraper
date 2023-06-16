import json

def get_config() -> dict:
    with open('config.json', 'r') as f:
        j = json.load(f)
    return j

config = get_config()