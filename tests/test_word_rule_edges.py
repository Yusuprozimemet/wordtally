"""The word rule beyond ASCII: plan.md's `[A-Za-z0-9']+`, not Python's `\\w`.

Beside tests/contract/, which stays frozen. Its five cases are ASCII only, so `[\\w']+` passes them
(lab-notebook.md, Retrospective, open item 5); these cases fail it.
"""
import unittest

from wordtally.count import words


class WordRuleEdgesTest(unittest.TestCase):
    def test_an_underscore_splits_a_word(self):
        self.assertEqual(words("snake_case"), ["snake", "case"])

    def test_an_accented_letter_splits_a_word(self):
        self.assertEqual(words("café naïve"), ["caf", "na", "ve"])

    def test_a_non_latin_word_is_no_word(self):
        self.assertEqual(words("слово word"), ["word"])

    def test_a_non_ascii_digit_is_no_word(self):
        self.assertEqual(words("route ٦٦"), ["route"])


if __name__ == "__main__":
    unittest.main()
