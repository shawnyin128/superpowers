"""Byte-parity guard for the canonical Plan summary fence.

The Plan summary template lives in two places:
  - agent-templates/sp-planner.md  (used by three-agent mode subagent)
  - skills/single-agent-development/SKILL.md  (used by single-agent main session)

Both copies MUST be byte-identical so the format cannot drift between
modes. A single-source-of-truth refactor is preferred, but until then
this test catches divergence the moment one copy is edited without the
other.

The fence is identified by an exact opening literal `📋 Plan:` and ends
at the next ``` fence close at the same indentation.
"""
from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SP_PLANNER = REPO_ROOT / "agent-templates" / "sp-planner.md"
SINGLE_AGENT = REPO_ROOT / "skills" / "single-agent-development" / "SKILL.md"

_FENCE_OPEN = re.compile(r"^(\s*)```output-template\s*$")
_FENCE_CLOSE = re.compile(r"^(\s*)```\s*$")


def extract_plan_summary_fence(path: pathlib.Path) -> str:
    """Return the first output-template fence body containing the
    canonical Plan summary opener (`📋 Plan:`).
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = _FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        indent = m.group(1)
        body: list[str] = []
        j = i + 1
        while j < len(lines):
            close = _FENCE_CLOSE.match(lines[j])
            if close and close.group(1) == indent:
                break
            body.append(lines[j])
            j += 1
        joined = "\n".join(body)
        if "📋 Plan:" in joined:
            return joined
        i = j + 1
    raise AssertionError(
        f"no output-template fence containing '📋 Plan:' found in {path}"
    )


class TestPlanSummaryFenceParity(unittest.TestCase):
    def test_both_files_have_the_fence(self):
        # Sanity — both files exist and contain the fence
        self.assertTrue(SP_PLANNER.exists(), f"missing {SP_PLANNER}")
        self.assertTrue(SINGLE_AGENT.exists(), f"missing {SINGLE_AGENT}")
        extract_plan_summary_fence(SP_PLANNER)
        extract_plan_summary_fence(SINGLE_AGENT)

    def test_fences_byte_identical(self):
        a = extract_plan_summary_fence(SP_PLANNER)
        b = extract_plan_summary_fence(SINGLE_AGENT)
        self.assertEqual(
            a,
            b,
            "Plan summary fence drifted between\n"
            f"  {SP_PLANNER}\n"
            f"  {SINGLE_AGENT}\n"
            "Both copies must stay byte-identical. Edit one, mirror the other.",
        )


if __name__ == "__main__":
    unittest.main()
