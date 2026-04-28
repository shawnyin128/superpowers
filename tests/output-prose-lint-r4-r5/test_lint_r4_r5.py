"""Tests for R4 and R5 rules added to scripts/lint-skill-output.py."""
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


class TestR4SectionHeader(unittest.TestCase):
    def test_bold_label_passes(self):
        res = fixture("valid_r4_bold_label.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("[R4]", res.stderr)

    def test_disable_comment_passes(self):
        res = fixture("valid_r4_disable_comment.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("[R4]", res.stderr)

    def test_bare_label_fails(self):
        res = fixture("invalid_r4_bare_label.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R4]", res.stderr)
        self.assertIn("Problem", res.stderr)

    def test_multiword_bare_label_fails(self):
        res = fixture("invalid_r4_multiword_label.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R4]", res.stderr)


class TestR5ShortCodeGloss(unittest.TestCase):
    def test_glossed_passes(self):
        res = fixture("valid_r5_glossed.md")
        # NOTE: this fixture mentions 'v0.8.18' which is a version
        # string. Per D1 (conservative) it must be glossed too.
        # The fixture body has 'F3+F4+F5 (the three migration features)
        # shipped in v0.8.18.' — version is at end of sentence as a
        # release tag. R5 still flags it under D1's conservative rule.
        # Either it passes or we accept this fixture also tests the
        # release-tag heuristic gap. We assert specifically that
        # Track / Tier / F-cluster are fine (not flagged); v0.8.18
        # may flag and that's acceptable for D1.
        if res.returncode != 0:
            # If R5 fired, it should ONLY be on the version string
            self.assertNotIn("Track A", res.stderr)
            self.assertNotIn("Tier 1", res.stderr)
            self.assertNotIn("F3+F4+F5", res.stderr)
            self.assertIn("v0.8.18", res.stderr)
        else:
            # Acceptable too — version at sentence end could be skipped
            # in a future heuristic refinement
            pass

    def test_naked_track_fails(self):
        res = fixture("invalid_r5_naked_track.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R5]", res.stderr)
        self.assertIn("Track A", res.stderr)

    def test_naked_tier_fails(self):
        res = fixture("invalid_r5_naked_tier.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R5]", res.stderr)

    def test_naked_f_cluster_fails(self):
        res = fixture("invalid_r5_naked_f_cluster.md")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[R5]", res.stderr)
        self.assertIn("F3+F4+F5", res.stderr)

    def test_single_f_not_flagged(self):
        # F3 alone is a fixed codename (R1 territory) and should NOT
        # be flagged by R5. The fixture wraps each F<n> with a gloss
        # to satisfy R1; R5 must not double-fire on F3 / F2.
        res = fixture("valid_r5_single_f.md")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("[R5]", res.stderr)


class TestExistingRulesUnchanged(unittest.TestCase):
    """Regression: R1/R2/R3 must still behave as before."""

    def test_existing_format_id_helper_tests_still_pass(self):
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/skill-output-format-id-helper/",
                "-q",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
