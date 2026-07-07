from __future__ import annotations
from agents.behavioral_agent import BehavioralSignalAgent
from agents.fusion_agent import FusionAgent
from agents.join_pattern_agent import JoinPatternAgent
from agents.metadata_agent import MetadataMatchAgent
from agents.transcript_agent import TranscriptSignalAgent
from meeting_state import MeetingState


class Orchestrator:
    def __init__(self, state: MeetingState):
        self.state = state
        self.agents = [
            MetadataMatchAgent(),
            TranscriptSignalAgent(),
            BehavioralSignalAgent(),
            JoinPatternAgent(),
        ]
        self.fusion = FusionAgent()
        self.history: list[dict] = []
    def apply_event(self, event: dict) -> dict:
        self._mutate_state(event)
        evidence = []
        for agent in self.agents:
            evidence.extend(agent.analyze(self.state))
        result = self.fusion.fuse(self.state, evidence)

        snapshot = {
            "event": event,
            "status": result.status,
            "selected_participant_id": result.selected_participant_id,
            "explanation": result.explanation,
            "participants": [
                {
                    "participant_id": v.participant_id,
                    "display_name": v.display_name,
                    "confidence": round(v.confidence, 4),
                    "raw_score": round(v.raw_score, 3),
                    "top_reasons": v.top_reasons,
                }
                for v in result.verdicts
            ],
        }
        self.history.append(snapshot)
        return snapshot
    
    def _mutate_state(self, event: dict) -> None:
        t = event["t"]
        etype = event["type"]
        pid = event.get("participant_id")

        if etype == "join":
            self.state.upsert_participant(pid, event["display_name"], t)
        elif etype == "leave":
            p = self.state.participants.get(pid)
            if p:
                p.left_at = t
        elif etype == "display_name_change":
            p = self.state.participants.get(pid)
            if p:
                p.display_name = event["display_name"]
                p.display_name_history.append((t, event["display_name"]))
        elif etype == "webcam":
            p = self.state.participants.get(pid)
            if p:
                p.webcam_on = event["on"]
        elif etype == "screen_share":
            for other in self.state.participants.values():
                other.is_screen_sharing = False
            p = self.state.participants.get(pid)
            if p:
                p.is_screen_sharing = event["on"]
        elif etype == "speech":
            p = self.state.participants.get(pid)
            if p:
                p.speaking_seconds += event.get("duration_sec", 0.0)
                if event.get("text"):
                    p.utterances.append((t, event["text"]))

        self.state.event_log.append(event)