"""Evaluator tests for humanized query.py output (features + todos)."""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FEATURES_QUERY = REPO_ROOT / "skills" / "manage-features" / "scripts" / "query.py"
TODOS_QUERY = REPO_ROOT / "skills" / "manage-todos" / "scripts" / "query.py"


def run(script, args, cwd):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        (self.tmp / ".claude").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


FEATURES_SEED = {
    "features": [
        {"id": "alpha", "category": "infrastructure", "priority": "high",
         "depends_on": [], "supersedes": [], "from_todo": None,
         "description": "Alpha description",
         "display_name": "Alpha Label",
         "steps": ["one"], "passes": True},
        {"id": "beta", "category": "infrastructure", "priority": "high",
         "depends_on": ["alpha"], "supersedes": [], "from_todo": None,
         "description": "Beta description",
         "display_name": "Beta Label",
         "steps": ["one"], "passes": False},
        {"id": "gamma", "category": "testing", "priority": "low",
         "depends_on": [], "supersedes": [], "from_todo": None,
         "description": "Gamma no display name", "steps": ["one"], "passes": False},
    ]
}


class TestFeaturesQuery(TempRepo):
    def setUp(self):
        super().setUp()
        (self.tmp / ".claude" / "features.json").write_text(json.dumps(FEATURES_SEED))

    def test_list_leads_with_display_name(self):
        res = run(FEATURES_QUERY, ["list", "--passes=false"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        out = res.stdout
        self.assertIn("Beta Label", out)
        first_beta_line = next(l for l in out.splitlines() if "Beta" in l)
        self.assertIn("[high]", first_beta_line)
        self.assertNotIn("beta", first_beta_line.replace("Beta", ""))
        self.assertIn("id: beta", out)

    def test_list_deps_render_as_display_name(self):
        res = run(FEATURES_QUERY, ["list", "--passes=false"], self.tmp)
        self.assertIn("deps: Alpha Label", res.stdout)

    def test_list_fallback_to_id_when_display_name_missing(self):
        res = run(FEATURES_QUERY, ["list", "--passes=false"], self.tmp)
        self.assertIn("gamma", res.stdout)

    def test_json_format_unchanged(self):
        res = run(FEATURES_QUERY, ["list", "--passes=false", "--format=json"], self.tmp)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        ids = {f["id"] for f in data}
        self.assertEqual(ids, {"beta", "gamma"})
        self.assertEqual(data[0]["display_name"], "Beta Label")

    def test_get_table_humanized(self):
        res = run(FEATURES_QUERY, ["get", "beta", "--format=table"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = res.stdout.splitlines()
        self.assertEqual(lines[0], "Beta Label")
        self.assertIn("id: beta", res.stdout)
        self.assertIn("Depends on: Alpha Label", res.stdout)

    def test_get_json_has_display_name(self):
        res = run(FEATURES_QUERY, ["get", "beta", "--format=json"], self.tmp)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["display_name"], "Beta Label")

    def test_next_table_humanized(self):
        res = run(FEATURES_QUERY, ["next", "--format=table"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(res.stdout.startswith("Beta Label"))


TODOS_SEED = {
    "todos": [
        {"id": "foo-id", "description": "Some description",
         "display_name": "Foo Label",
         "category": "tech-debt", "status": "pending", "notes": "",
         "created_at": "2026-01-01T00:00:00Z",
         "linked_feature_ids": [], "archived_feature_paths": []},
        {"id": "bar-id", "description": "Bar no display name",
         "category": "feature-idea", "status": "pending", "notes": "",
         "created_at": "2026-01-01T00:00:00Z",
         "linked_feature_ids": ["x", "y"], "archived_feature_paths": []},
    ]
}


class TestTodosQuery(TempRepo):
    def setUp(self):
        super().setUp()
        (self.tmp / ".claude" / "todos.json").write_text(json.dumps(TODOS_SEED))

    def test_list_leads_with_display_name(self):
        res = run(TODOS_QUERY, ["list"], self.tmp)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Foo Label", res.stdout)
        self.assertIn("id: foo-id", res.stdout)

    def test_list_fallback_to_id(self):
        res = run(TODOS_QUERY, ["list"], self.tmp)
        self.assertIn("bar-id", res.stdout)

    def test_linked_count_preserved(self):
        res = run(TODOS_QUERY, ["list"], self.tmp)
        self.assertIn("[2 linked]", res.stdout)

    def test_json_unchanged(self):
        res = run(TODOS_QUERY, ["list", "--format=json"], self.tmp)
        data = json.loads(res.stdout)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["display_name"], "Foo Label")


class TestSKILLTemplateUpdates(unittest.TestCase):
    """Smoke checks that SKILL.md files got the humanized commit template."""

    def _read(self, rel):
        return (REPO_ROOT / rel).read_text()

    def test_feature_tracker_uses_humanized_commit(self):
        content = self._read("skills/feature-tracker/SKILL.md")
        self.assertIn('complete \\"{display_name}\\" ({feature-id})', content)
        self.assertNotIn("mark {feature-id} as complete", content)

    def test_single_agent_commit_template(self):
        content = self._read("skills/single-agent-development/SKILL.md")
        self.assertIn('complete "<display_name>" (<feature-id>)', content)
        self.assertNotIn("mark <feature-id> as complete", content)

    def test_three_agent_commit_template(self):
        content = self._read("skills/three-agent-development/SKILL.md")
        self.assertIn('complete "<display_name>" (<feature-id>)', content)
        self.assertNotIn("mark <feature-id> as complete", content)


if __name__ == "__main__":
    unittest.main()
