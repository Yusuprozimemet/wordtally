"""build.py's parsing and its swap rule. Run: python -m unittest experiments/jev/e1/test_build.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

LINES = [
    "- [x] C9.1 **hold** — the rest stands: the suite passes.",
    "      broken: a line edited → removed=1",
    "      broken: a line added, the near miss → removed=0",
    "      (The near miss ran with the check inverted, so that",
    "      \"failed\" means the grep counted 0.)",
    "      Evidence: after #1, OK.",
]

SOURCE = '''def run():
    pass


class CliTest(unittest.TestCase):
    def test_one(self):
        self.assertEqual(1, 1)

    def test_two(self):
        pass
'''


class BuildTest(unittest.TestCase):
    def test_the_criterion_stops_at_its_evidence_and_drops_the_tick(self):
        self.assertEqual(build.criterion_text(LINES), "C9.1 **hold** — the rest stands: the suite passes.")

    def test_breaks_and_a_note_across_lines(self):
        broken, notes = build.breaks_and_notes(LINES)
        self.assertEqual(broken, [("a line edited", "removed=1"), ("a line added, the near miss", "removed=0")])
        self.assertEqual(notes, ['(The near miss ran with the check inverted, so that "failed" means the grep counted 0.)'])

    def test_a_method_ends_where_the_next_begins(self):
        self.assertEqual(build.method(SOURCE, "CliTest", "test_one"),
                         "    def test_one(self):\n        self.assertEqual(1, 1)")
        self.assertIsNone(build.method(SOURCE, "CliTest", "test_three"))

    def test_a_swap_never_stays_on_its_day_or_touches_what_it_breaks(self):
        found = {
            "C1.1": {"day": "01", "files": ["wordtally/__main__.py"]},
            "C1.2": {"day": "01", "files": ["tests/contract/x.py", "wordtally/count.py"]},
            "C2.3": {"day": "02", "files": ["wordtally/__main__.py"]},
            "C2.1": {"day": "02", "files": ["wordtally/__main__.py"]},
            "C2.2": {"day": "02", "files": ["tests/contract/x.py"]},
            "C2.4": {"day": "02", "files": ["tests/test_cli.py"]},
        }
        # C1.2's count.py break would rotate onto C2.3, whose input a split changes.
        self.assertEqual(build.swaps(found), [
            ("C1.1", 0, "C2.2"), ("C1.2", 0, "C2.1"), ("C1.2", 1, "C2.1"),
            ("C2.3", 0, "C1.2"), ("C2.1", 0, "C1.2"), ("C2.2", 0, "C1.1"), ("C2.4", 0, "C1.2")])


if __name__ == "__main__":
    unittest.main()
