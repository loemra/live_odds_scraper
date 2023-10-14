from dataclasses import dataclass


@dataclass
class Match:
    match: str
    potential: str
    result: bool
