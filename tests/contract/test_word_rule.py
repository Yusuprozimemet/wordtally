"""The word rule: what counts as a word. Frozen; never edited (CLAUDE.md, plan.md)."""
import unittest

from wordtally.count import words


class WordRuleTest(unittest.TestCase):
    def test_an_apostrophe_stays_inside_a_word(self):
        self.assertEqual(words("don't stop"), ["don't", "stop"])

    def test_a_hyphen_splits_a_word(self):
        self.assertEqual(words("e-mail"), ["e", "mail"])

    def test_digits_are_word_characters(self):
        self.assertEqual(words("route 66"), ["route", "66"])

    def test_punctuation_and_space_only_separate(self):
        self.assertEqual(words("  Hello,\tworld!\n"), ["Hello", "world"])

    def test_case_is_kept(self):
        self.assertEqual(words("The the"), ["The", "the"])


if __name__ == "__main__":
    unittest.main()
