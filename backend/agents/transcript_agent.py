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
    r"\bwelcome,? ([a-z]+(?: [a-z]+){0,2})",
    r"\bthanks for joining,? ([a-z]+(?: [a-z]+){0,2})",
    r"\bso ([a-z]+(?: [a-z]+){0,2}),? (?:can you|tell us|walk us)",
]