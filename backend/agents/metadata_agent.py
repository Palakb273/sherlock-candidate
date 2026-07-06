from __future__ import annotations
import difflib
import re
from agents.base import Agent, Evidence


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _tokens(s: str) -> set[str]:
    return set(_normalize(s).split())


def name_similarity(a: str, b: str) -> float:
    a_n, b_n = _normalize(a), _normalize(b)
    if not a_n or not b_n:
        return 0.0
    if a_n == b_n:
        return 1.0
    ta, tb = _tokens(a), _tokens(b)
    if ta and tb:
        overlap = len(ta & tb) / max(len(ta), len(tb))
    else:
        overlap = 0.0
    seq_ratio = difflib.SequenceMatcher(None, a_n, b_n).ratio()
    return max(overlap, seq_ratio * 0.8)

class MetadataMatchAgent(Agent):
    """Compares each participant's display name against known candidate/interviewer names."""

    name = "metadata_agent"
    default_weight = 0.35

    DEVICE_NAME_PATTERNS = [
        r"macbook", r"iphone", r"ipad", r"windows", r"dell", r"lenovo", r"hp laptop",
        r"^room\b", r"^conference", r"unknown", r"^guest\b", r"^participant\b",
    ]

    def analyze(self, state) -> list[Evidence]:
        out: list[Evidence] = []
        candidate_name = state.meta.candidate_name
        candidate_email_user = state.meta.candidate_email.split("@")[0]
        interviewers = state.meta.interviewer_names

        for p in state.participants.values():
            name = p.display_name
            is_device_name = any(re.search(pat, name.lower()) for pat in self.DEVICE_NAME_PATTERNS)

            if is_device_name:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="device_like_display_name", score=0.0, weight=self.default_weight * 0.4,
                    explanation=f'Display name "{name}" looks like a device/OS default, not a person name.',
                    confidence_in_signal=0.6,
                ))
                continue
            sim_candidate = max(
                name_similarity(name, candidate_name),
                name_similarity(name, candidate_email_user),
            )
            sim_interviewer = max((name_similarity(name, iv) for iv in interviewers), default=0.0)

            if sim_interviewer > 0.75 and sim_interviewer > sim_candidate:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="matches_known_interviewer", score=-0.8, weight=self.default_weight,
                    explanation=f'Display name "{name}" closely matches a known interviewer name.',
                    confidence_in_signal=0.8,
                ))
            elif sim_candidate >= 0.6:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="matches_candidate_metadata", score=sim_candidate, weight=self.default_weight,
                    explanation=f'Display name "{name}" matches candidate record ("{candidate_name}", {state.meta.candidate_email}) with similarity {sim_candidate:.2f}.',
                    confidence_in_signal=0.7,
                ))
            elif sim_candidate > 0.0:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="weak_name_partial_match", score=sim_candidate * 0.5, weight=self.default_weight * 0.5,
                    explanation=f'Display name "{name}" only weakly resembles candidate name "{candidate_name}".',
                    confidence_in_signal=0.4,
                ))
            else:
                out.append(Evidence(
                    participant_id=p.participant_id, agent=self.name,
                    signal="no_name_match", score=-0.1, weight=self.default_weight * 0.3,
                    explanation=f'Display name "{name}" does not resemble candidate or interviewer names.',
                    confidence_in_signal=0.3,
                ))
        return out