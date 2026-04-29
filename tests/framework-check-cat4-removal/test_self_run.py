"""Structural self-run proxy for framework-check-cat4-removal.

Rather than executing the framework-check skill (which is an LLM-driven
workflow), this test parses skills/framework-check/SKILL.md and asserts
that the report-template fence emits exactly the category list the
SKILL declares — and that no Cat 4 / 'Agent templates' / '[4/9] Agent
templates' tokens leak into either the live category headings or the
rendered report fences.
"""
from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "framework-check" / "SKILL.md"


class TestReportRendersSparseCategories(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def _output_template_blocks(self) -> list[str]:
        return re.findall(
            r"```output-template\n(.*?)```",
            self.text,
            re.DOTALL,
        )

    def test_no_cat4_agent_templates_label_in_any_fence(self):
        for block in self._output_template_blocks():
            self.assertNotIn(
                "[4/9] Agent templates",
                block,
                "Cat 4 'Agent templates' label still rendered in an "
                "output-template fence",
            )

    def test_no_cat4_agent_templates_8_denominator_either(self):
        # Defensive: catch any future renumbering that brings back the
        # category under a [4/8] label.
        for block in self._output_template_blocks():
            self.assertNotIn("[4/8] Agent templates", block)

    def test_report_template_carries_retired_stub(self):
        # At least one fence must contain the canonical retired stub
        # (Step 2 template + the example block). Both should carry it.
        stub = "[4/9] (slot retired — see CHANGELOG)"
        hits = sum(1 for b in self._output_template_blocks() if stub in b)
        self.assertGreaterEqual(
            hits,
            2,
            "expected the retired-slot stub in both the Step 2 template "
            "and the example block",
        )

    def test_category_labels_in_template_match_live_headings(self):
        # The live "### N." sequence and the fenced "[N/9]" labels must
        # agree on which category numbers are active. Slot 4 is retired,
        # so it appears in fences only as the stub line and never as a
        # numbered category heading.
        live_nums = sorted(
            {
                int(m.group(1))
                for m in re.finditer(r"^### (\d+)\.", self.text, re.MULTILINE)
            }
        )
        # Find numeric labels [N/9] inside output-template fences,
        # excluding the stub form "[4/9] (slot retired ...)".
        template_nums: set[int] = set()
        for block in self._output_template_blocks():
            for m in re.finditer(r"\[(\d+)/9\][^\n]*", block):
                line = m.group(0)
                if "slot retired" in line:
                    continue
                template_nums.add(int(m.group(1)))
        self.assertEqual(set(live_nums), template_nums)

    def test_category_count_heading_matches_live_categories(self):
        m = re.search(r"## Check Categories \((\d+)\)", self.text)
        self.assertIsNotNone(m)
        declared = int(m.group(1))
        live_nums = {
            int(mm.group(1))
            for mm in re.finditer(r"^### (\d+)\.", self.text, re.MULTILINE)
        }
        self.assertEqual(declared, len(live_nums))


if __name__ == "__main__":
    unittest.main()
