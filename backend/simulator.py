from __future__ import annotations
import time
from meeting_state import ExternalMetadata, MeetingState

def _base_meta(start_offset=0.0):
    now = time.time() + start_offset
    return ExternalMetadata(
        candidate_name="Riya Sharma",
        candidate_email="riya.sharma@gmail.com",
        interviewer_names=["Alex Chen", "Priya Nair"],
        scheduled_start_epoch=now,
    )


SCENARIOS = {}

SCENARIOS["device_name"] = {
    "title": 'Candidate joins as "MacBook Pro"',
    "description": "Display name gives zero signal; identity resolves once the transcript starts.",
    "meta": _base_meta(),
    "events": [
        {"t": 0, "type": "join", "participant_id": "p1", "display_name": "Alex Chen"},
        {"t": 2, "type": "join", "participant_id": "p2", "display_name": "MacBook Pro"},
        {"t": 4, "type": "webcam", "participant_id": "p2", "on": True},
        {"t": 6, "type": "speech", "participant_id": "p1", "duration_sec": 4,
         "text": "Hi, thanks for joining, can you introduce yourself?"},
        {"t": 10, "type": "speech", "participant_id": "p2", "duration_sec": 6,
         "text": "Hi, my name is Riya Sharma, thanks for having me today."},
        {"t": 18, "type": "speech", "participant_id": "p2", "duration_sec": 20,
         "text": "I've been working on full-stack projects using FastAPI and React for the past year."},
        {"t": 40, "type": "speech", "participant_id": "p1", "duration_sec": 5,
         "text": "Great, let's start with a coding question."},
    ],
}

