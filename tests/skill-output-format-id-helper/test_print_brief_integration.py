"""Integration tests for print-brief.py after migration to _lib.format_id.

Verifies:
  1. Output structure unchanged for a normal feature with display_name.
  2. Unknown feature raises a clean error (no silent fallback to bare id).
  3. Empty display_name raises (impossible after backfill, but enforced).
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
PRINT_BRIEF = REPO_ROOT / "skills" / "feature-tracker" / "scripts" / "print-brief.py"


def run(args, cwd):
    return subprocess.run(
        [sys.executable, str(PRINT_BRIEF), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


PLAN_FIXTURE = """plan_id: demo-feat
iteration: 1
based_on: docs/design-docs/example.md

problem: |
  A short problem statement for the demo feature.

steps:
  - id: S1
    desc: Do the thing
    approach: |
      Implement the demo step.
    test_plan:
      - happy path

execution:
  S1:
    status: done
    confidence: 95
    notes: implemented cleanly
    commits: [abc1234]

eval:
  rounds:
    - round: 1
      verdict: PASS
"""


class _TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / ".claude").mkdir()
        archive = self.tmp / ".claude" / "agents" / "state" / "archive" / "demo-feat"
        archive.mkdir(parents=True)
        (archive / "demo-feat.plan.yaml").write_text(PLAN_FIXTURE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_features(self, payload):
        (self.tmp / ".claude" / "features.json").write_text(json.dumps(payload))


class TestPrintBriefIntegration(_TempRepo):
    def test_output_includes_display_name_for_known_feature(self):
        self.write_features({"features": [
            {"id": "demo-feat", "display_name": "Demo readable name"},
        ]})
        res = run(["demo-feat", "--commit=abc1234"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Demo readable name", res.stdout)
        # Existing format preserves display_name in the title position
        self.assertIn("Feature complete", res.stdout)

    def test_unknown_feature_fails_loudly(self):
        self.write_features({"features": []})
        res = run(["demo-feat", "--commit=abc1234"], self.tmp)
        # Should fail rather than silently print bare id
        self.assertNotEqual(res.returncode, 0)

    def test_empty_display_name_fails(self):
        self.write_features({"features": [
            {"id": "demo-feat", "display_name": ""},
        ]})
        res = run(["demo-feat", "--commit=abc1234"], self.tmp)
        self.assertNotEqual(res.returncode, 0)

    def test_explicit_display_name_override_still_works(self):
        # When --display-name is provided, lookup is skipped entirely
        self.write_features({"features": []})  # no entry
        res = run(["demo-feat", "--commit=abc1234",
                   "--display-name=Override label"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Override label", res.stdout)


if __name__ == "__main__":
    unittest.main()
