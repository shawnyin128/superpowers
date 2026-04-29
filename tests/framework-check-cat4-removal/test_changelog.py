"""CHANGELOG regression for framework-check-cat4-removal.

Asserts that the Cat 4 retirement is recorded under an Unreleased
section in CHANGELOG.md.
"""
from __future__ import annotations

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


class TestChangelogEntry(unittest.TestCase):
    def setUp(self):
        self.text = CHANGELOG.read_text(encoding="utf-8")

    def test_unreleased_section_present(self):
        self.assertTrue(
            re.search(r"^## Unreleased\b", self.text, re.MULTILINE),
            "CHANGELOG.md must have an Unreleased section",
        )

    def test_cat4_retirement_recorded(self):
        # The Unreleased entry must mention Cat 4 retirement in some form.
        # Match any of the canonical phrasings: "Cat 4" + "retired"/"deleted"/"removed"
        # appearing inside the Unreleased section.
        m = re.search(
            r"^## Unreleased\b(.*?)(?=^## )",
            self.text,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(m, "Unreleased section not found")
        body = m.group(1)
        self.assertRegex(
            body,
            r"Cat 4",
            "Unreleased section must reference 'Cat 4'",
        )
        self.assertRegex(
            body,
            r"retired|deleted|removed",
            "Unreleased section must describe Cat 4 as retired/deleted/removed",
        )


if __name__ == "__main__":
    unittest.main()
