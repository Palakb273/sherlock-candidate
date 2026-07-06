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