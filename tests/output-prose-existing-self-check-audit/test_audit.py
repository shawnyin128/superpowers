"""Regression tests for the existing self-check audit + augmentation.

Eight existing locations in skills/ used a generic 'Self-check before
print: re-read aloud as if to a colleague' rule. F5 augments each with
a one-line cross-reference to the central specific-pattern rule shipped
in F4 (using-sp-harness/SKILL.md). This test asserts the cross-reference
is present in each augmented location AND the original generic rule
is preserved.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest


def _normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs (including newlines) to single
    spaces, so substring search tolerates wrapped prose."""
    return re.sub(r"\s+", " ", text)

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT_OUTPUT = REPO_ROOT / "scripts" / "lint-skill-output.py"
LINT_PROCEDURAL = REPO_ROOT / "scripts" / "lint-skill-procedural.py"

# Eight files audited in F5.
AUDITED_FILES = [
    "skills/audit-feedback/SKILL.md",
    "skills/feature-tracker/SKILL.md",
    "skills/switch-dev-mode/SKILL.md",
    "skills/finishing-a-development-branch/SKILL.md",
    "skills/three-agent-development/SKILL.md",
    "skills/sp-planner-role/SKILL.md",
    "skills/sp-evaluator-role/SKILL.md",
    "skills/brainstorming/SKILL.md",
    "skills/framework-check/SKILL.md",
]

CROSS_REFERENCE_PHRASE = "specific-pattern self-check from"
SOURCE_FILENAME = "using-sp-harness/SKILL.md"
GENERIC_RULE_FRAGMENT = "as if to a colleague"


@pytest.mark.parametrize("path", AUDITED_FILES)
def test_cross_reference_added(path: str) -> None:
    """Each audited file must contain the cross-reference phrase
    naming using-sp-harness/SKILL.md as the source."""
    text = _normalize_whitespace(
        (REPO_ROOT / path).read_text(encoding="utf-8")
    )
    assert CROSS_REFERENCE_PHRASE in text, (
        f"{path} missing cross-reference phrase "
        f"{CROSS_REFERENCE_PHRASE!r}"
    )
    assert SOURCE_FILENAME in text, (
        f"{path} cross-reference must name {SOURCE_FILENAME}"
    )


@pytest.mark.parametrize("path", AUDITED_FILES)
def test_generic_rule_preserved(path: str) -> None:
    """AUGMENT, not REPLACE — the generic 're-read aloud' rule must
    still be present in each file."""
    text = _normalize_whitespace(
        (REPO_ROOT / path).read_text(encoding="utf-8")
    )
    assert GENERIC_RULE_FRAGMENT in text, (
        f"{path} lost the generic 're-read aloud as if to a colleague' "
        f"rule (we AUGMENT, not REPLACE)"
    )


def test_lint_skill_output_full_tree_passes() -> None:
    res = subprocess.run(
        [sys.executable, str(LINT_OUTPUT), "--quiet", "--no-schema-check"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr


def test_lint_skill_procedural_full_tree_passes() -> None:
    res = subprocess.run(
        [sys.executable, str(LINT_PROCEDURAL), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
