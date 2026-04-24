"""Evaluator checks for brainstorming SKILL.md display_name guidance."""
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "brainstorming" / "SKILL.md"


class TestBrainstormingSkill(unittest.TestCase):
    def setUp(self):
        self.content = SKILL.read_text()

    def test_add_example_includes_display_name_as_required(self):
        block = re.search(
            r"```bash\s*\npython3 .+?manage-features.+?mutate\.py\" add.*?```",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(block, "could not find mutate.py add code block")
        text = block.group(0)
        self.assertIn("--display-name=", text)
        m = re.search(r"^\s*(\[--display-name)", text, re.MULTILINE)
        self.assertIsNone(m, "--display-name should not be in [brackets] (required, not optional)")

    def test_rules_mention_noun_phrase_guidance(self):
        self.assertIn("noun phrase", self.content)
        self.assertRegex(self.content, r"display_name.+noun phrase|noun phrase.+display_name")

    def test_rules_show_verb_vs_noun_example(self):
        self.assertRegex(self.content, r"✅.*\n.*❌|❌.*\n.*✅|✅.*·.*❌|❌.*·.*✅")


if __name__ == "__main__":
    unittest.main()
