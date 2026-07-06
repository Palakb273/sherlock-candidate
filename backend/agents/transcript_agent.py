from __future__ import annotations
import json
import os
import re
from agents.base import Agent, Evidence

SELF_INTRO_PATTERNS = [
    r"\bmy name is ([a-z]+(?: [a-z]+){0,2})(?:,| and | here | speaking|\.)",
    r"\bi'?m ([a-z]+(?: [a-z]+){0,2}),? (?:and )?i'?ll be (?:the candidate|interviewing)",
    r"\bthis is ([a-z]+(?: [a-z]+){0,2}) speaking",
    r"\bi am ([a-z]+(?: [a-z]+){0,2}),? here for the (?:interview|position|role)",
]

THIRD_PERSON_INTRO_PATTERNS = [
    r"\bwelcome,? ([a-z]+(?: [a-z]+){0,2}),",
    r"\bthanks for joining,? ([a-z]+(?: [a-z]+){0,2}),",
    r"\bso ([a-z]+(?: [a-z]+){0,2}),\s*(?:can you|tell us|walk us)",
]

class TranscriptSignalAgent(Agent):
    """Reads the speaker-attributed transcript for direct evidence of identity."""

    name = "transcript_agent"
    default_weight = 0.55

    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self._client = None
        if self.groq_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.groq_key)
            except Exception:
                self._client = None
    
    def analyze(self, state) -> list[Evidence]:
        out: list[Evidence] = []
        candidate_name = state.meta.candidate_name
        active = state.active_participants()

        for p in active:
            if not p.utterances:
                continue
            recent_text = " ".join(text for _, text in p.utterances[-6:])

            addressed_name = self._extract_addressed_as(recent_text)
            if addressed_name:
                from agents.metadata_agent import name_similarity
                sim_to_candidate = name_similarity(addressed_name, candidate_name)
                if sim_to_candidate >= 0.5:
                    target = self._best_other_match(active, p.participant_id, addressed_name)
                    if target:
                        out.append(Evidence(
                            participant_id=target.participant_id, agent=self.name,
                            signal="addressed_by_candidate_name", score=0.75, weight=self.default_weight * 0.9,
                            explanation=f'Was addressed as "{addressed_name}" by another participant, matching candidate record "{candidate_name}".',
                            confidence_in_signal=0.7,
                        ))
        return out

    def _best_other_match(self, active, speaker_id, name):
        """Among active participants other than the speaker, find whichever
        one's current display name best matches `name`."""
        from agents.metadata_agent import name_similarity
        candidates = [p for p in active if p.participant_id != speaker_id]
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        return max(candidates, key=lambda p: name_similarity(p.display_name, name))
    def _extract_addressed_as(self, text: str) -> str | None:
        low = text.lower()
        for pat in THIRD_PERSON_INTRO_PATTERNS:
            m = re.search(pat, low)
            if m:
                return m.group(1).title()
        return None