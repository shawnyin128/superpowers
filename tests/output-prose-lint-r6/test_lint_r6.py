"""Tests for R6 (fancy/curly quote ban) in scripts/lint-skill-output.py."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
LINT = REPO_ROOT / "scripts" / "lint-skill-output.py"
FIXTURES = pathlib.Path(__file__).resolve().parent / "lint-fixtures"


def fixture(name, *extra):
    return subprocess.run(
        [
            sys.executable,
            str(LINT),
            "--no-schema-check",
            "--paths",
            str(FIXTURES / name),
            *extra,
        ],
        capture_output=True,
        text=True,
    )


class TestR6FancyQuotes(unittest.TestCase):
    def test_ascii_only_passes(self):
        res = fixture("valid_r6_ascii.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("[R6]", res.stderr)

    def test_curly_double_fails(self):
        res = fixture("invalid_r6_curly_double.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R6]", res.stderr)
        # Both opening and closing curly doubles should be flagged
        self.assertIn("U+201C", res.stderr)
        self.assertIn("U+201D", res.stderr)

    def test_curly_single_fails(self):
        res = fixture("invalid_r6_curly_single.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R6]", res.stderr)
        self.assertIn("U+2018", res.stderr)
        self.assertIn("U+2019", res.stderr)

    def test_disable_comment_passes(self):
        res = fixture("valid_r6_disable_comment.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("[R6]", res.stderr)


if __name__ == "__main__":
    unittest.main()
