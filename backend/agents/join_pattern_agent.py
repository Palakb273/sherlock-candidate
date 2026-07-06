from __future__ import annotations

from agents.base import Agent, Evidence


class JoinPatternAgent(Agent):
    """Looks at join timing and count of interview-shaped participants."""

    name = "join_pattern_agent"
    default_weight = 0.15

    ON_TIME_WINDOW_SEC = 5 * 60

    def analyze(self, state) -> list[Evidence]:
        out: list[Evidence] = []
        scheduled = state.meta.scheduled_start_epoch
        for p in state.active_participants():
            delta = abs(p.joined_at - scheduled)
            if delta <= self.ON_TIME_WINDOW_SEC:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="joined_near_scheduled_time", score=0.2, weight=self.default_weight,
                    explanation="Joined within 5 minutes of the scheduled interview start time.",
                    confidence_in_signal=0.4,
                ))
            else:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="joined_off_schedule", score=-0.1, weight=self.default_weight * 0.5,
                    explanation="Joined well outside the scheduled start window.",
                    confidence_in_signal=0.3,
                ))
        return out