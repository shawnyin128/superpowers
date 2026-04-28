"""Regression tests for the section header migration to '**Label**' style.

Asserts that:
  - Full skills/ tree exits 0 with lint-skill-output.py (no R1/R2/R4/R5
    failures); restores the previously-red guard installed by F1.
  - Each of the 7 originally-violating labels now appears in
    '**Label**' form in its respective file (and the bare 'Label:'
    form does NOT appear in the surrounding output-template fence).
  - print-brief.py emits '**What:**' (bold with colon) instead of
    bare 'What:' for each Feature Brief field.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"
PRINT_BRIEF = REPO_ROOT / "skills" / "feature-tracker" / "scripts" / "print-brief.py"

BRAINSTORMING = REPO_ROOT / "skills" / "brainstorming" / "SKILL.md"
FINISHING = REPO_ROOT / "skills" / "finishing-a-development-branch" / "SKILL.md"
FEATURE_TRACKER = REPO_ROOT / "skills" / "feature-tracker" / "SKILL.md"


def test_full_tree_lint_passes() -> None:
    """The 'lint-skill-output passes on full skills/ tree' regression
    that F1 left red is now green after F2 migration."""
    res = subprocess.run(
        [sys.executable, str(LINT), "--quiet", "--no-schema-check"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"full skills/ tree fails lint-skill-output.py: {res.stderr}"
    )


@pytest.mark.parametrize("label", [
    "Problem",
    "Approach",
    "Key decisions made",
    "Divergence risks",
    "Scope",
    "Options",
])
def test_brainstorming_label_migrated(label: str) -> None:
    text = BRAINSTORMING.read_text(encoding="utf-8")
    assert f"**{label}**" in text, (
        f"brainstorming/SKILL.md missing '**{label}**' bold form"
    )
    # Confirm bare 'Label:' on its own line is gone for the migrated
    # labels (allowing prose-context use elsewhere if any).
    bare_at_eol = re.compile(rf"^\s*{re.escape(label)}:\s*$", re.MULTILINE)
    assert not bare_at_eol.search(text), (
        f"brainstorming/SKILL.md still has bare '{label}:' on its own "
        f"line; should be '**{label}**'"
    )


def test_finishing_branch_label_migrated() -> None:
    text = FINISHING.read_text(encoding="utf-8")
    assert "**This will permanently delete**" in text
    assert "This will permanently delete:" not in text


def test_print_brief_emits_bold_labels() -> None:
    """print-brief.py emits '**Label:**' bold form."""
    grammar = PRINT_BRIEF.read_text(encoding="utf-8")
    for label in ("What", "Steps", "Files", "Tests", "Rounds", "Followups", "Commit"):
        assert f"**{label}:**" in grammar, (
            f"print-brief.py output line for {label} must use "
            f"'**{label}:**' bold form"
        )
        # Confirm the bare-form line is gone
        bare_pattern = re.compile(rf'f"{label}:\s+\{{', re.MULTILINE)
        assert not bare_pattern.search(grammar), (
            f"print-brief.py still has bare '{label}:' line"
        )


def test_feature_tracker_reference_template_matches() -> None:
    """The feature-tracker/SKILL.md reference template (showing what
    print-brief emits) must match the script's actual emission style."""
    text = FEATURE_TRACKER.read_text(encoding="utf-8")
    for label in ("What", "Steps", "Files", "Tests", "Rounds", "Followups", "Commit"):
        assert f"**{label}:**" in text, (
            f"feature-tracker/SKILL.md reference template must use "
            f"'**{label}:**' bold form to match print-brief.py output"
        )
