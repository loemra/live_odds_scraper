import json
import random


def get_random_user_agent():
    with open("packages/util/userAgents.json", "r") as f:
        j = json.load(f)

    return random.choice(j)
