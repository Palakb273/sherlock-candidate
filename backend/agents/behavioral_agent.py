from __future__ import annotations
from agents.base import Agent, Evidence


class BehavioralSignalAgent(Agent):
    """Uses non-linguistic behavior: who talks the most, webcam usage, screen share."""

    name = "behavioral_agent"
    default_weight = 0.3

    def analyze(self, state) -> list[Evidence]:
        out: list[Evidence] = []
        active = state.active_participants()
        if not active:
            return out

        total_speaking = sum(p.speaking_seconds for p in active) or 1.0

        for p in active:
            share = p.speaking_seconds / total_speaking
            if p.speaking_seconds == 0 and len(active) > 1:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="silent_observer", score=-0.6, weight=self.default_weight,
                    explanation="Has not spoken at all while others are talking -- looks like a silent observer.",
                    confidence_in_signal=0.5,
                ))
                continue

            score = 0.0
            reasons = []
            if share >= 0.4:
                score += 0.5
                reasons.append(f"accounts for {share:.0%} of all speaking time")
            elif share <= 0.1:
                score -= 0.3
                reasons.append(f"only {share:.0%} of speaking time")

            if p.webcam_on:
                score += 0.15
                reasons.append("webcam is on")
            if p.is_screen_sharing:
                score += 0.1
                reasons.append("currently screen-sharing")

            score = max(-1.0, min(1.0, score))
            out.append(Evidence(
                participant_id=p.participant_id, agent=self.name,
                signal="speaking_and_presence_pattern", score=score, weight=self.default_weight,
                explanation="Behavioral pattern: " + ", ".join(reasons) + ".",
                confidence_in_signal=0.5,
            ))
        return out