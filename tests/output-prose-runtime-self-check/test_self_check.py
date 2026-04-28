"""Regression tests for the runtime self-check section in using-sp-harness.

The section codifies a specific-pattern self-check rule that covers
free-form chat output (where lint-skill-output.py R5 cannot scan).
The pre-design experiment validated 3/3 PASS for this rule shape.
This test locks the section's structure so the rule cannot drift
silently.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "using-sp-harness" / "SKILL.md"
LINT_OUTPUT = REPO_ROOT / "scripts" / "lint-skill-output.py"
LINT_PROCEDURAL = REPO_ROOT / "scripts" / "lint-skill-procedural.py"

# Mirrors lint-skill-procedural.py's _FENCE_OPEN_RE.
_PROC_FENCE_RE = re.compile(
    r"^\s*```procedural-instruction\s*$", re.MULTILINE
)


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_section_heading_present(skill_text: str) -> None:
    assert "## Output prose self-check (free-form chat)" in skill_text


def test_all_four_pattern_strings_referenced(skill_text: str) -> None:
    """The procedural-instruction fence must list all 4 pattern types."""
    proc_idx = skill_text.index("```procedural-instruction")
    fence_close = skill_text.index("\n```\n", proc_idx)
    fence_body = skill_text[proc_idx:fence_close]
    for pattern in (
        r"Track [A-Z]",
        r"Tier \d+",
        r"F\d+(\+F\d+)+",
        r"v\d+\.\d+\.\d+",
    ):
        assert pattern in fence_body, (
            f"procedural-instruction fence missing pattern: {pattern!r}"
        )


def test_worked_example_demonstrates_compliance(skill_text: str) -> None:
    """The worked-example sample must contain Track / Tier / F-cluster /
    version examples each with a parenthesized gloss."""
    we_idx = skill_text.index("```worked-example")
    we_close = skill_text.index("\n```\n", we_idx)
    body = skill_text[we_idx:we_close]
    # Spot-check at least one glossed instance of each pattern.
    # Allow gloss to follow on the same line OR after a line break +
    # indented continuation (matches R5's _GLOSS_AFTER_RE 8-char window).
    def followed_by_gloss(token: str) -> bool:
        idx = body.find(token)
        if idx < 0:
            return False
        tail = body[idx + len(token) : idx + len(token) + 12]
        return bool(re.match(r"\s{0,8}\(", tail))

    assert followed_by_gloss("Track A")
    assert followed_by_gloss("F3+F4+F5")
    assert followed_by_gloss("Tier 1")
    assert followed_by_gloss("v0.8.19") or followed_by_gloss("v0.8.18")


def test_using_sp_harness_has_exactly_one_procedural_fence(
    skill_text: str,
) -> None:
    """Exactly ONE procedural-instruction fence — locks the section's
    fence count so a future author who adds a second fence without
    explicit test update gets caught."""
    count = len(_PROC_FENCE_RE.findall(skill_text))
    assert count == 1, (
        f"using-sp-harness/SKILL.md must have exactly 1 "
        f"procedural-instruction fence (the new self-check rule); "
        f"found {count}"
    )


def test_lint_skill_procedural_passes() -> None:
    res = subprocess.run(
        [sys.executable, str(LINT_PROCEDURAL), "--paths", str(SKILL)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr


def test_lint_skill_output_passes() -> None:
    res = subprocess.run(
        [
            sys.executable,
            str(LINT_OUTPUT),
            "--paths",
            str(SKILL),
            "--no-schema-check",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
