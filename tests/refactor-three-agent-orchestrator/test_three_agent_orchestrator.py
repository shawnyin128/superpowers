"""Round 1 evaluation tests for refactor-three-agent-orchestrator."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "three-agent-development" / "SKILL.md"
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"


class TestStepDispatchesUseGeneralPurpose(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def _section(self, heading: str, next_heading: str) -> str:
        m = re.search(
            rf"## {re.escape(heading)}.*?(?=^## {re.escape(next_heading)})",
            self.text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(m, f"section '{heading}' not found")
        return m.group(0)

    def test_step_2_dispatches_general_purpose_with_planner_role(self):
        s = self._section("Step 2: Dispatch Planner", "Step 3:")
        self.assertIn("subagent_type='general-purpose'", s)
        self.assertIn("sp-harness:sp-planner-role", s)

    def test_step_3_dispatches_general_purpose_with_generator_role(self):
        s = self._section("Step 3: Dispatch Generator", "Step 4:")
        self.assertIn("subagent_type='general-purpose'", s)
        self.assertIn("sp-harness:sp-generator-role", s)

    def test_step_4_dispatches_general_purpose_with_evaluator_role(self):
        s = self._section("Step 4: Dispatch Evaluator", "Step 5:")
        self.assertIn("subagent_type='general-purpose'", s)
        self.assertIn("sp-harness:sp-evaluator-role", s)

    def test_no_at_agent_dispatch_remains(self):
        # The legacy '@agent sp-X' pattern should be gone now.
        self.assertNotRegex(
            self.text,
            r"@agent\s+sp-(planner|generator|evaluator)\b",
            "legacy '@agent sp-*' dispatch verb still present",
        )


class TestSubagentDispatchContractPresent(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_dispatch_contract_section_exists(self):
        self.assertIn("## Subagent Dispatch Contract", self.text)

    def test_retry_protocol_documented(self):
        # The contract MUST describe the retry-on-skip behavior.
        self.assertRegex(
            self.text,
            r"[Rr]etry.{0,20}stronger.{0,20}prompt",
            "Subagent Dispatch Contract missing retry-with-stronger-prompt protocol description",
        )

    def test_blocked_phase_terminal_state_named(self):
        # On second-attempt failure, the phase MUST be marked BLOCKED.
        self.assertIn("BLOCKED", self.text)


class TestObsoleteSubagentDefinitionsSectionRemoved(unittest.TestCase):
    def test_subagent_definitions_section_gone(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("## Subagent Definitions", text)

    def test_no_dot_claude_agents_path_references(self):
        # `.claude/agents/sp-{role}.md` paths must not appear in the
        # orchestrator any more — those files no longer exist.
        text = SKILL.read_text(encoding="utf-8")
        for role in ("sp-planner", "sp-generator", "sp-evaluator"):
            self.assertNotIn(
                f".claude/agents/{role}.md",
                text,
                f"orchestrator still references obsolete .claude/agents/{role}.md path",
            )


class TestOrchestratorPreservedConcerns(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_protocol_marker_preserved(self):
        # framework-check Cat 9 requires the literal protocol string.
        self.assertIn("decision-touchpoint-protocol", self.text)

    def test_max_rounds_safeguard_kept_at_orchestrator(self):
        self.assertIn("Max Rounds Safeguard", self.text)
        self.assertIn("5 rounds completed", self.text)

    def test_agent_independence_section_preserved(self):
        self.assertIn("## Agent Independence", self.text)

    def test_role_skills_section_replaces_subagent_definitions(self):
        self.assertIn("## Role Skills", self.text)


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
