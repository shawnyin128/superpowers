"""Deterministic heuristic to derive a short display_name from a description.

Kept standalone (no imports from sibling skill dirs) because each skill
directory is independently distributable in the plugin bundle.
"""
from __future__ import annotations

import re

LEADING_VERBS = frozenset({
    "add", "build", "fix", "write", "create", "update", "implement",
    "refactor", "remove", "support", "make", "author", "introduce",
    "enable", "extend",
})

MAX_LEN = 50


def derive_display_name(description: str) -> str:
    if description is None:
        return ""
    s = description.strip()
    s = re.sub(r"[\s\.;:,!?\-–—]+$", "", s)
    if not s:
        return ""

    tokens = s.split(None, 1)
    if len(tokens) == 2 and tokens[0].lower() in LEADING_VERBS:
        stripped = tokens[1].lstrip()
        if stripped:
            s = stripped[:1].upper() + stripped[1:]

    if len(s) <= MAX_LEN:
        return s

    cut = s[:MAX_LEN]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    cut = cut.rstrip(" ,.;:-–—")
    return cut or s[:MAX_LEN]
