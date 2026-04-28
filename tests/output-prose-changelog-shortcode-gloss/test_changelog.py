"""Regression test for CHANGELOG.md short-code gloss discipline.

CHANGELOG.md is the GitHub repo landing-page artifact. Naked
project-internal short codes (without inline gloss) leak meaning to
public readers who lack the maintainer's context. This test asserts:

- Backtick-quoted occurrences (code-spans, fenced blocks) are
  excluded from the naked-use scan — they describe patterns,
  not reference clusters.
- Stripped-text matches of `F\\d+\\+F\\d+`, `F\\d+-F\\d+`,
  `Track [A-Z]`, `Tier \\d+` must each be immediately followed by
  a parenthesized gloss.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _strip_code_spans_and_fences(text: str) -> str:
    """Remove fenced code blocks (```…```, ````…````) and inline
    backtick-quoted spans (`…`). Replace each with a single space so
    content boundaries remain meaningful."""
    text = re.sub(r"````[\s\S]*?````", " ", text)
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`\n]*`", " ", text)
    return text


_FOLLOWED_BY_GLOSS = re.compile(r"\s{0,8}\(")


def _matches_without_gloss(text: str, pattern: re.Pattern) -> list[str]:
    fails: list[str] = []
    for m in pattern.finditer(text):
        tail = text[m.end() : m.end() + 16]
        if _FOLLOWED_BY_GLOSS.match(tail):
            continue
        ctx_start = max(0, m.start() - 30)
        ctx_end = min(len(text), m.end() + 30)
        fails.append(
            f"{m.group(0)!r} at offset {m.start()} not followed by "
            f"gloss (context: ...{text[ctx_start:ctx_end]!r}...)"
        )
    return fails


def test_no_naked_f_cluster() -> None:
    text = _strip_code_spans_and_fences(CHANGELOG.read_text(encoding="utf-8"))
    pattern = re.compile(r"\bF\d+(?:\+F\d+)+\b")
    fails = _matches_without_gloss(text, pattern)
    assert not fails, "Naked F+F cluster references in CHANGELOG.md:\n" + "\n".join(fails)


def test_no_naked_f_range() -> None:
    text = _strip_code_spans_and_fences(CHANGELOG.read_text(encoding="utf-8"))
    pattern = re.compile(r"\bF\d+-F\d+\b")
    fails = _matches_without_gloss(text, pattern)
    assert not fails, "Naked F-range references in CHANGELOG.md:\n" + "\n".join(fails)


def test_no_naked_track() -> None:
    text = _strip_code_spans_and_fences(CHANGELOG.read_text(encoding="utf-8"))
    pattern = re.compile(r"\bTrack [A-Z]\b")
    fails = _matches_without_gloss(text, pattern)
    assert not fails, "Naked Track references in CHANGELOG.md:\n" + "\n".join(fails)


def test_no_naked_tier() -> None:
    text = _strip_code_spans_and_fences(CHANGELOG.read_text(encoding="utf-8"))
    pattern = re.compile(r"\bTier \d+\b")
    fails = _matches_without_gloss(text, pattern)
    assert not fails, "Naked Tier references in CHANGELOG.md:\n" + "\n".join(fails)
