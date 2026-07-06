from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Evidence:
    """A single weak signal about a single participant, emitted by one agent."""

    participant_id: str
    agent: str                 # which agent produced this, e.g. "transcript_agent"
    signal: str                # short machine name, e.g. "self_introduction_match"
    score: float                # in [-1, 1]. Positive = "is the candidate", negative = "is not"
    weight: float                # how much this agent's opinion should matter, in [0, 1]
    explanation: str             # human-readable reason, shown in the UI
    confidence_in_signal: float = 1.0   # how sure the agent itself is about this reading, [0,1]

@dataclass
class ParticipantSnapshot:
    """Everything we currently know about one participant, updated as events arrive."""

    participant_id: str
    display_name: str
    joined_at: float
    left_at: Optional[float] = None
    webcam_on: bool = False
    is_screen_sharing: bool = False
    speaking_seconds: float = 0.0
    utterances: list = field(default_factory=list)   # list of (t, text)
    display_name_history: list = field(default_factory=list)  # name changes over time

class Agent:
    """Base class every signal agent implements."""

    name: str = "base_agent"
    default_weight: float = 0.5

    def analyze(self, state: "MeetingState") -> list[Evidence]:
        raise NotImplementedError