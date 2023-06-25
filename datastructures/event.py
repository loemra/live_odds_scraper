from dataclasses import dataclass, field
from datetime import datetime
from market import Market
from event_metadata import EventMetadata


@dataclass
class Event:
    metadata: EventMetadata
    markets: dict[str, Market] = field(default_factory=dict)
