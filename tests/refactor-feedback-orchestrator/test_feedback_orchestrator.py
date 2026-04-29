"""Round 1 evaluation tests for refactor-feedback-orchestrator."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "feedback" / "SKILL.md"
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"


class TestDispatchUsesGeneralPurposeWithRoleSkill(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_dispatch_uses_general_purpose_subagent(self):
        self.assertIn("subagent_type='general-purpose'", self.text)

    def test_dispatch_targets_sp_feedback_role(self):
        self.assertIn("sp-harness:sp-feedback-role", self.text)

    def test_no_legacy_at_agent_dispatch(self):
        self.assertNotRegex(
            self.text,
            r"@agent\s+sp-feedback\b",
            "legacy '@agent sp-feedback' dispatch verb still present",
        )

    def test_dispatch_passes_mode_flag(self):
        # The prompt must explicitly pass mode='B' so the role skill
        # knows which mode to run.
        self.assertIn("mode='B'", self.text)


class TestObsoleteVerifyStepRemoved(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_no_verify_section_heading(self):
        self.assertNotIn("Verify sp-feedback exists", self.text)

    def test_no_per_project_agent_path_reference(self):
        # `.claude/agents/sp-feedback.md` paths must not appear in the
        # orchestrator any more — that file no longer exists post-migration.
        self.assertNotIn(".claude/agents/sp-feedback.md", self.text)


class TestStepRenumberingClean(unittest.TestCase):
    def test_steps_are_consecutive_starting_from_1(self):
        text = SKILL.read_text(encoding="utf-8")
        step_numbers = [
            int(m.group(1))
            for m in re.finditer(r"^## Step (\d+):", text, re.MULTILINE)
        ]
        self.assertGreaterEqual(len(step_numbers), 5,
                                "feedback skill should have at least 5 steps")
        # Steps must be a consecutive run starting at 1
        self.assertEqual(
            step_numbers,
            list(range(1, len(step_numbers) + 1)),
            f"step numbering not consecutive from 1: {step_numbers}",
        )


class TestDispatchContractReferencePresent(unittest.TestCase):
    def test_references_three_agent_dispatch_contract(self):
        text = SKILL.read_text(encoding="utf-8")
        # Reference to the contract is mandatory — DRY across orchestrators.
        self.assertIn("Subagent Dispatch Contract", text)


class TestLintClean(unittest.TestCase):
    def test_lint_exits_zero(self):
        res = subprocess.run(
            [sys.executable, str(LINT), "--no-schema-check", "--paths", str(SKILL)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stderr)


if __name__ == "__main__":
    unittest.main()
