"""Regression tests for the agent-templates lint-scope extension.

F2 (section header migration) missed agent-templates/sp-planner.md and
agent-templates/sp-evaluator.md because lint-skill-output.py's
default_skill_files() globbed only skills/*/SKILL.md. This feature
extends the default scope to include agent-templates/*.md AND migrates
the planner/evaluator brief fences from plain ``` to ```output-template
plus the necessary **Label** wrapping.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"
PLANNER = REPO_ROOT / "agent-templates" / "sp-planner.md"
EVALUATOR = REPO_ROOT / "agent-templates" / "sp-evaluator.md"


def test_default_scope_includes_agent_templates() -> None:
    """Default lint scope, queried via --check JSON output, must
    cover both skills/*/SKILL.md AND agent-templates/*.md.

    Counts the actual SKILL.md and agent-template files on disk and
    asserts files_scanned matches their sum, so any drift in the
    glob pattern is caught."""
    skill_count = len(list((REPO_ROOT / "skills").glob("*/SKILL.md")))
    agent_template_count = len(
        list((REPO_ROOT / "agent-templates").glob("*.md"))
    )
    expected_total = skill_count + agent_template_count
    assert agent_template_count > 0, (
        "agent-templates/*.md missing — test fixture broken"
    )

    res = subprocess.run(
        [sys.executable, str(LINT), "--check", "--no-schema-check"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    import json
    payload = json.loads(res.stdout)
    assert payload["files_scanned"] == expected_total, (
        f"default scope scanned {payload['files_scanned']} files; "
        f"expected {expected_total} (skills={skill_count} + "
        f"agent-templates={agent_template_count})"
    )


def test_planner_brief_uses_bold_labels() -> None:
    text = PLANNER.read_text(encoding="utf-8")
    assert "**Problem**" in text
    assert "**Key decisions**" in text
    assert "**Options**" in text
    # Bare 'Problem:' / 'Key decisions:' / 'Options:' on their own line
    # must be gone.
    for label in ("Problem", "Key decisions", "Options"):
        bare = re.compile(rf"^\s*{re.escape(label)}:\s*$", re.MULTILINE)
        assert not bare.search(text), (
            f"sp-planner.md still has bare '{label}:' on its own line"
        )


def test_planner_uses_output_template_fence() -> None:
    """The planner brief must be in a ```output-template fence so
    the lint actually scans it."""
    text = PLANNER.read_text(encoding="utf-8")
    assert "```output-template" in text


def test_evaluator_uses_output_template_fence() -> None:
    text = EVALUATOR.read_text(encoding="utf-8")
    # Two output-template fences — one for ITERATE, one for PASS.
    fence_count = text.count("```output-template")
    assert fence_count >= 2, (
        f"sp-evaluator.md should have at least 2 ```output-template "
        f"fences (ITERATE + PASS); found {fence_count}"
    )


def test_default_scope_lint_passes() -> None:
    """Default-scope lint exits 0 with --no-schema-check (R3 warnings
    do not change exit code; we accept warnings here)."""
    res = subprocess.run(
        [sys.executable, str(LINT), "--quiet", "--no-schema-check"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, (
        f"default-scope lint failed: stderr=\n{res.stderr}"
    )
