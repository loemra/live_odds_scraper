from dataclasses import dataclass, field
from typing import Dict, Hashable


@dataclass
class EventRegistration:
    sb_event_id: Hashable
    unified_event_id: int

    sb_to_unified_selection: Dict[Hashable, Hashable] = field(
        default_factory=dict
    )
    unified_to_sb_selection: Dict[Hashable, Hashable] = field(
        default_factory=dict
    )
