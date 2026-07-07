from __future__ import annotations
import math
from collections import defaultdict
from dataclasses import dataclass, field
from agents.base import Evidence


@dataclass
class ParticipantVerdict:
    participant_id: str
    display_name: str
    raw_score: float
    confidence: float
    top_reasons: list[str] = field(default_factory=list)
    all_evidence: list[Evidence] = field(default_factory=list)

class FusionAgent:
    CONFIDENT_MARGIN = 0.30
    CONFIDENT_FLOOR = 0.45

    def fuse(self, state, evidence: list[Evidence]):
        by_participant: dict[str, list[Evidence]] = defaultdict(list)
        for e in evidence:
            by_participant[e.participant_id].append(e)

        active = state.active_participants()
        raw_scores: dict[str, float] = {}
        for p in active:
            ev = by_participant.get(p.participant_id, [])
            raw_scores[p.participant_id] = sum(e.score * e.weight * e.confidence_in_signal for e in ev)