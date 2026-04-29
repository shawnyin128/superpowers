"""Round 1 evaluation tests for refactor-single-agent-orchestrator.

After the rewrite, skills/single-agent-development/SKILL.md must:
  1. Dispatch each role phase to the corresponding sp-{role}-role skill
     via Skill(sp-harness:sp-<role>-role) invocation.
  2. NOT contain the canonical Plan summary fence opener — it lives in
     sp-planner-role now.
  3. NOT contain the inline 'Mandatory adversarial protocol' header —
     it lives in sp-evaluator-role now.
  4. STILL contain the decision-touchpoint-protocol marker (Cat 9).
  5. STILL pass lint-skill-output.py.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "single-agent-development" / "SKILL.md"
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"


class TestOrchestratorDispatchesToRoleSkills(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_planner_phase_dispatches_to_sp_planner_role(self):
        m = re.search(
            r"## Step 2:.*?(?=^## Step 3:)",
            self.text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(m, "Step 2 section not found")
        self.assertIn("Skill(sp-harness:sp-planner-role)", m.group(0))

    def test_generator_phase_dispatches_to_sp_generator_role(self):
        m = re.search(
            r"## Step 3:.*?(?=^## Step 4:)",
            self.text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(m, "Step 3 section not found")
        self.assertIn("Skill(sp-harness:sp-generator-role)", m.group(0))

    def test_evaluator_phase_dispatches_to_sp_evaluator_role(self):
        m = re.search(
            r"## Step 4:.*?(?=^## Step 5:)",
            self.text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(m, "Step 4 section not found")
        self.assertIn("Skill(sp-harness:sp-evaluator-role)", m.group(0))


class TestInlineRoleContentRemoved(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_canonical_plan_summary_fence_opener_absent(self):
        # The literal "📋 Plan: <display_name>" line is the canonical
        # Plan summary fence opener and must live only in sp-planner-role.
        self.assertNotIn(
            "📋 Plan: <display_name>",
            self.text,
            "canonical Plan summary fence opener still present in orchestrator",
        )

    def test_mandatory_adversarial_protocol_absent(self):
        self.assertNotIn(
            "Mandatory adversarial protocol",
            self.text,
            "Evaluator's adversarial protocol still inlined in orchestrator",
        )


class TestProtocolMarkerPreserved(unittest.TestCase):
    def test_decision_touchpoint_protocol_marker_present(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn(
            "decision-touchpoint-protocol",
            text,
            "framework-check Cat 9 protocol marker missing — orchestrator "
            "must contain the literal string somewhere in its body",
        )


class TestLintClean(unittest.TestCase):
    def test_lint_exits_zero_on_rewritten_orchestrator(self):
        res = subprocess.run(
            [sys.executable, str(LINT), "--no-schema-check", "--paths", str(SKILL)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)


if __name__ == "__main__":
    unittest.main()
