"""Regression tests for the 'Output Prose Discipline' chapter in
writing-skills/SKILL.md."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "writing-skills" / "SKILL.md"
LINT_OUTPUT = REPO_ROOT / "scripts" / "lint-skill-output.py"
LINT_PROCEDURAL = REPO_ROOT / "scripts" / "lint-skill-procedural.py"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def chapter_text(skill_text: str) -> str:
    start = skill_text.index("## Output Prose Discipline")
    end = skill_text.index("## The Bottom Line", start)
    return skill_text[start:end]


def test_chapter_present(chapter_text: str) -> None:
    assert chapter_text.startswith("## Output Prose Discipline")


def test_three_required_subsections(chapter_text: str) -> None:
    for heading in (
        "### Section header style",
        "### Short-code glossing",
        "### Why generic self-checks fail",
    ):
        assert heading in chapter_text, f"missing subsection {heading!r}"


def test_cross_links_to_sibling_chapters(chapter_text: str) -> None:
    """Chapter must name OTR and PSR at the top so authors find the
    other discipline chapters."""
    intro = chapter_text[: chapter_text.index("### ")]
    assert "Output Template Rules" in intro
    assert "Procedural Section Rules" in intro


def test_all_four_pattern_strings_listed(chapter_text: str) -> None:
    """The Short-code glossing subsection must list the same four
    patterns the lint and runtime self-check enforce."""
    short_code_section_start = chapter_text.index("### Short-code glossing")
    short_code_section_end = chapter_text.index(
        "### Why generic self-checks fail"
    )
    body = chapter_text[short_code_section_start:short_code_section_end]
    for pattern in (
        r"Track [A-Z]",
        r"Tier \d+",
        # F-cluster pattern: chapter prose may render the regex with
        # or without parens around the +F\d+ group, so use a tolerant check
        r"F\d+\+F\d+",
        r"v\d+\.\d+\.\d+",
    ):
        assert pattern in body, (
            f"Short-code glossing subsection missing pattern: {pattern!r}"
        )


def test_chapter_contains_no_anti_example_markers(chapter_text: str) -> None:
    """Per Procedural Section Rules' no-anti-example rule (and for
    consistency across discipline chapters), this chapter does not
    use ❌ markers."""
    assert "❌" not in chapter_text
    # 'BAD' as a standalone label
    assert not re.search(r"\bBAD\b", chapter_text)


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


def test_lint_skill_procedural_passes() -> None:
    res = subprocess.run(
        [sys.executable, str(LINT_PROCEDURAL), "--paths", str(SKILL)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
