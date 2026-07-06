from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from agents.base import ParticipantSnapshot


@dataclass
class ExternalMetadata:
    """Info Sherlock already has before the meeting starts, from calendar/ATS."""
    candidate_name: str
    candidate_email: str
    interviewer_names: list[str]
    scheduled_start_epoch: float


@dataclass
class MeetingState:
    meta: ExternalMetadata
    started_at: float = field(default_factory=time.time)
    participants: dict[str, ParticipantSnapshot] = field(default_factory=dict)
    event_log: list[dict] = field(default_factory=list)

    def upsert_participant(self, participant_id: str, display_name: str, t: float) -> ParticipantSnapshot:
        p = self.participants.get(participant_id)
        if p is None:
            p = ParticipantSnapshot(participant_id=participant_id, display_name=display_name, joined_at=t)
            p.display_name_history.append((t, display_name))
            self.participants[participant_id] = p
        return p

    def active_participants(self) -> list[ParticipantSnapshot]:
        return [p for p in self.participants.values() if p.left_at is None]