"""The word rule and the counts."""
import re

# A word is a run of letters, digits and apostrophes: "don't" is one, "e-mail" two.
# tests/contract/ pins this rule; it is never changed in place.
WORD = re.compile(r"[A-Za-z0-9']+")


def words(text):
    """The words of text, in order, as they appear."""
    return WORD.findall(text)


def count_words(text):
    return len(words(text))


def counts(text):
    """Lines, words and characters of text, as `wc` counts lines: newlines."""
    return text.count("\n"), count_words(text), len(text)
