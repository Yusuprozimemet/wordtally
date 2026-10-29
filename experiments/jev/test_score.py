"""score.py's counting. Run: python -m unittest experiments/jev/test_score.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score  # noqa: E402


def case(i, kind, label, **kw):
    return {"id": i, "kind": kind, "label": label, "compound": False, **kw}


def rec(answer, probability, recommendation, error=None):
    return {"answer": answer, "probability": probability, "recommendation": recommendation,
            "abstained": False, "error": error, "cost_usd": None, "seconds": None}


CASES = [case("R01", "real", "supports"), case("R02", "real", "supports"),
         case("R03", "real", "supports", ambiguous=True), case("R04", "real", "insufficient"),
         case("I01", "insufficient", "insufficient"), case("X01", "contradicts", "contradicts"),
         case("S01", "swapped", "unrelated")]
RECS = {"R01": rec("supports", 0.95, "pass"), "R02": rec("supports", 0.8, "flag"),
        "R03": rec("insufficient", 0.7, "flag"), "R04": rec("insufficient", 0.7, "flag"),
        "I01": rec("supports", 0.95, "pass"), "X01": rec("contradicts", 0.6, "flag"),
        "S01": rec(None, None, None, error="HTTP 500")}


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = score.score(CASES, RECS)

    def test_hard_cases_are_the_hand_written_kinds_not_real_cases_labelled_insufficient(self):
        self.assertEqual((self.s["hard_flagged"], self.s["hard"]), (1, 2))
        self.assertEqual((self.s["real_insufficient_flagged"], self.s["real_insufficient"]), (1, 1))

    def test_a_false_alarm_is_a_flag_on_a_real_supports_case_and_ambiguous_ones_are_apart(self):
        self.assertEqual((self.s["false_alarms"], self.s["supports"]), (1, 2))
        self.assertIn("R03 (supports): insufficient 0.7", self.s["ambiguous"])

    def test_an_error_is_neither_a_flag_nor_answered(self):
        self.assertEqual((self.s["answered"], self.s["errors"]), (5, 1))
