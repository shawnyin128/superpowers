"""Unit tests for skills/_lib/format_id.py."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "skills"))

from _lib.format_id import format_id, get_display_name  # noqa: E402


class _ChdirTempRepo(unittest.TestCase):
    """Switch cwd to a tmp dir with a .claude/ for path resolution."""

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / ".claude").mkdir()
        self._old_cwd = pathlib.Path.cwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_features(self, payload):
        (self.tmp / ".claude" / "features.json").write_text(json.dumps(payload))

    def write_todos(self, payload):
        (self.tmp / ".claude" / "todos.json").write_text(json.dumps(payload))


class TestGetDisplayName(_ChdirTempRepo):
    def test_feature_happy_path(self):
        self.write_features({"features": [
            {"id": "f1", "display_name": "Shiny thing"},
        ]})
        self.assertEqual(get_display_name("f1", "feature"), "Shiny thing")

    def test_todo_happy_path(self):
        self.write_todos({"todos": [
            {"id": "t1", "display_name": "Investigate flake"},
        ]})
        self.assertEqual(get_display_name("t1", "todo"), "Investigate flake")

    def test_feature_id_missing_raises(self):
        self.write_features({"features": [
            {"id": "f1", "display_name": "Shiny thing"},
        ]})
        with self.assertRaises(ValueError) as ctx:
            get_display_name("does-not-exist", "feature")
        self.assertIn("does-not-exist", str(ctx.exception))

    def test_todo_id_missing_raises(self):
        self.write_todos({"todos": []})
        with self.assertRaises(ValueError) as ctx:
            get_display_name("missing", "todo")
        self.assertIn("missing", str(ctx.exception))

    def test_empty_display_name_raises(self):
        self.write_features({"features": [
            {"id": "f1", "display_name": ""},
        ]})
        with self.assertRaises(ValueError) as ctx:
            get_display_name("f1", "feature")
        self.assertIn("display_name", str(ctx.exception))

    def test_missing_display_name_key_raises(self):
        self.write_features({"features": [
            {"id": "f1"},
        ]})
        with self.assertRaises(ValueError):
            get_display_name("f1", "feature")

    def test_invalid_kind_raises(self):
        self.write_features({"features": []})
        with self.assertRaises(ValueError) as ctx:
            get_display_name("anything", "bogus")
        self.assertIn("kind", str(ctx.exception))

    def test_source_file_missing_raises(self):
        # No features.json written; .claude/ exists but is empty
        with self.assertRaises((FileNotFoundError, ValueError)):
            get_display_name("anything", "feature")

    def test_dual_source_disambiguation(self):
        self.write_features({"features": [
            {"id": "shared-id", "display_name": "Feature side"},
        ]})
        self.write_todos({"todos": [
            {"id": "shared-id", "display_name": "Todo side"},
        ]})
        self.assertEqual(get_display_name("shared-id", "feature"), "Feature side")
        self.assertEqual(get_display_name("shared-id", "todo"), "Todo side")

    def test_walks_up_from_subdir(self):
        # cwd is self.tmp; create a sub-sub dir and chdir into it
        self.write_features({"features": [
            {"id": "f1", "display_name": "Found from subdir"},
        ]})
        sub = self.tmp / "a" / "b" / "c"
        sub.mkdir(parents=True)
        os.chdir(sub)
        try:
            self.assertEqual(get_display_name("f1", "feature"), "Found from subdir")
        finally:
            os.chdir(self.tmp)


class TestFormatId(_ChdirTempRepo):
    def test_feature_format(self):
        self.write_features({"features": [
            {"id": "humanize-foo", "display_name": "Make foo readable"},
        ]})
        self.assertEqual(
            format_id("humanize-foo", "feature"),
            "humanize-foo(Make foo readable)",
        )

    def test_todo_format(self):
        self.write_todos({"todos": [
            {"id": "todo-bar", "display_name": "Investigate bar"},
        ]})
        self.assertEqual(
            format_id("todo-bar", "todo"),
            "todo-bar(Investigate bar)",
        )

    def test_propagates_value_error_from_lookup(self):
        self.write_features({"features": []})
        with self.assertRaises(ValueError):
            format_id("missing", "feature")


if __name__ == "__main__":
    unittest.main()
