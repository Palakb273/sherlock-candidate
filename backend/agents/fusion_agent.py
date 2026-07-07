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

@dataclass
class FusionResult:
    verdicts: list[ParticipantVerdict]
    status: str
    selected_participant_id: str | None
    explanation: str

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
        if not active:
            return FusionResult([], "insufficient_data", None, "No participants in the meeting yet.")

        temp = 1.0
        exp_scores = {pid: math.exp(s / temp) for pid, s in raw_scores.items()}
        total = sum(exp_scores.values()) or 1.0
        confidences = {pid: v / total for pid, v in exp_scores.items()}
        verdicts = []
        for p in active:
            ev = sorted(by_participant.get(p.participant_id, []), key=lambda e: -abs(e.score * e.weight))
            top_reasons = [e.explanation for e in ev[:3]]
            verdicts.append(ParticipantVerdict(
                participant_id=p.participant_id,
                display_name=p.display_name,
                raw_score=raw_scores[p.participant_id],
                confidence=confidences[p.participant_id],
                top_reasons=top_reasons,
                all_evidence=ev,
            ))
        verdicts.sort(key=lambda v: -v.confidence)

        if len(verdicts) == 1:
            solo = verdicts[0]
            if not solo.all_evidence or abs(solo.raw_score) < 0.05:
                return FusionResult(verdicts, "insufficient_data", None,
                                     "Only one participant present and no strong signal yet -- waiting for the candidate to join or speak.")
            if solo.raw_score < 0:
                return FusionResult(verdicts, "insufficient_data", None,
                                     f'Only "{solo.display_name}" is present, and evidence points to them being an interviewer, not the candidate -- waiting for the candidate to join.')
            return FusionResult(verdicts, "confident", solo.participant_id, self._explain(solo, "confident"))

        top = verdicts[0]
        second = verdicts[1] if len(verdicts) > 1 else None
        margin = top.confidence - (second.confidence if second else 0.0)

        if top.confidence >= self.CONFIDENT_FLOOR and margin >= self.CONFIDENT_MARGIN:
            status = "confident"
            selected = top.participant_id
            explanation = self._explain(top, status)
        elif top.confidence >= self.CONFIDENT_FLOOR * 0.7:
            status = "ambiguous"
            selected = None
            if second:
                explanation = (
                    f'Leaning towards "{top.display_name}" ({top.confidence:.0%}) but the lead over '
                    f'"{second.display_name}" ({second.confidence:.0%}) is not yet large enough to commit '
                    "-- collecting more signal."
                )
            else:
                explanation = "Only weak signal so far; waiting for more evidence."
        else:
            status = "ambiguous"
            selected = None
            explanation = "No participant has strong enough combined evidence yet; treating identity as unresolved."

        return FusionResult(verdicts, status, selected, explanation)

    def _explain(self, v: ParticipantVerdict, status: str) -> str:
        reasons = "; ".join(v.top_reasons) if v.top_reasons else "combined weak signals"
        return f'Identified "{v.display_name}" as the candidate with {v.confidence:.0%} confidence. Key evidence: {reasons}.'