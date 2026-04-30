"""Regression guard for retire-init-project-agent-files.

After the role-skill migration, agent-templates/ is gone and
init-project no longer emits per-project sp-*.md subagent files.
These assertions lock that state in: any future drift that
re-introduces an agent-templates/ reference in a load-bearing
surface will fail this test loudly.

Scope of "load-bearing surface" here is what the feature explicitly
cleaned up:
  * agent-templates/ directory itself
  * skills/init-project/SKILL.md (the previous emitter)
  * skills/framework-check/SKILL.md (Cat 5 / Cat 9 / Cat 9b scope)
  * skills/writing-skills/SKILL.md (frontmatter description)
  * scripts/lint-skill-output.py code path

Out of scope (intentional, must NOT be flagged):
  * docs/, CHANGELOG.md — historical references
  * tests/*/fixtures/ — verbatim archived plan YAMLs and similar
  * tests/skill-routing*, tests/skill-pruning* — gitignored tooling
  * tests/orchestrator-language-enforcement/test_lang_skill_text.py
    — mentions agent-templates/ in its module docstring as a
    historical pointer to where the fixture used to live
  * scripts/lint-skill-output.py docstring — historical pointer to
    where role bodies used to live; the executable code path is
    what this test guards
"""
from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestAgentTemplatesRetired(unittest.TestCase):

    def test_agent_templates_directory_removed(self):
        self.assertFalse(
            (REPO_ROOT / "agent-templates").exists(),
            "agent-templates/ directory must be removed; role bodies "
            "live in skills/sp-*-role/ now.",
        )

    def test_init_project_skill_no_agent_templates_reference(self):
        text = (REPO_ROOT / "skills" / "init-project" / "SKILL.md").read_text()
        self.assertNotIn(
            "agent-templates",
            text,
            "skills/init-project/SKILL.md must not reference agent-templates/.",
        )
        self.assertNotIn(
            ".claude/agents/sp-planner.md",
            text,
            "init-project must not emit .claude/agents/sp-planner.md.",
        )
        self.assertNotIn(
            ".claude/agents/sp-feedback.md",
            text,
            "init-project must not emit .claude/agents/sp-feedback.md.",
        )

    def test_framework_check_skill_no_agent_templates_reference(self):
        text = (REPO_ROOT / "skills" / "framework-check" / "SKILL.md").read_text()
        self.assertNotIn(
            "agent-templates",
            text,
            "skills/framework-check/SKILL.md must not reference "
            "agent-templates/ in scope or inventory.",
        )

    def test_writing_skills_description_no_agent_templates_reference(self):
        text = (REPO_ROOT / "skills" / "writing-skills" / "SKILL.md").read_text()
        # Restrict to frontmatter so a future body example mentioning
        # agent-templates/ as historical context does not fail.
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        self.assertIsNotNone(m, "writing-skills SKILL.md must have YAML frontmatter")
        frontmatter = m.group(1)
        self.assertNotIn(
            "agent-templates",
            frontmatter,
            "writing-skills frontmatter description must not list "
            "agent-templates/*.md as a target surface.",
        )

    def test_lint_skill_output_glob_excludes_agent_templates(self):
        text = (REPO_ROOT / "scripts" / "lint-skill-output.py").read_text()
        # Guard the executable code path, not the docstring. Slice the
        # function: from `def default_skill_files` to the next `def ` /
        # EOF, strip the leading triple-quoted docstring if present.
        start = text.find("def default_skill_files(")
        self.assertNotEqual(start, -1, "default_skill_files function must be present")
        rest = text[start:]
        next_def = rest.find("\ndef ", 1)
        body = rest if next_def == -1 else rest[:next_def]
        without_docstring = re.sub(r'"""[\s\S]*?"""', "", body, count=1)
        self.assertNotIn(
            "agent-templates",
            without_docstring,
            "default_skill_files executable body must not glob "
            "agent-templates/*.md any more.",
        )


if __name__ == "__main__":
    unittest.main()
