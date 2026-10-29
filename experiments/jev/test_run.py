"""run.py's rule, its parsing and its records. Run: python -m unittest experiments/jev/test_run.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

CASE = {"id": "R01", "commit": "abc", "bundle": {"criterion": "C1.1", "check": "", "breaks": [], "notes": []}}
KEY = "sk-or-not-a-real-key"


def reply(choice, probs, model="typesafe/jev-1.14-20261001", cost=0.00002):
    return 200, json.dumps({"model": model, "answers": {"verdict": {
        "type": "choice", "choice": choice, "confidence": 0.5, "probabilities": probs}},
        "usage": {"input_tokens": 400, "output_tokens": 70, "cost": cost}})


class RubricTest(unittest.TestCase):
    def test_the_question_and_the_four_labels_come_from_the_rubric(self):
        question, labels = run.rubric()
        self.assertTrue(question.startswith("Here is an acceptance criterion"), question)
        self.assertTrue(question.endswith("the probability that your answer is right."), question)
        self.assertEqual(set(labels), {"supports", "insufficient", "contradicts", "unrelated"})


class RecommendationTest(unittest.TestCase):
    def test_supports_at_or_above_the_threshold_passes(self):
        self.assertEqual(run.recommendation("supports", 0.9), "pass")

    def test_supports_below_the_threshold_is_a_flag(self):
        self.assertEqual(run.recommendation("supports", 0.89), "flag")

    def test_any_other_answer_is_a_flag_however_sure(self):
        self.assertEqual(run.recommendation("unrelated", 1.0), "flag")

    def test_an_abstention_is_a_flag(self):
        self.assertEqual(run.recommendation(None, None), "flag")


class ParseTest(unittest.TestCase):
    def test_an_answer_keeps_its_probability_snapshot_and_cost(self):
        r = run.parse_jev(*reply("insufficient", {"supports": 0.3, "insufficient": 0.7}))
        self.assertEqual((r["answer"], r["probability"], r["served"], r["cost_usd"]),
                         ("insufficient", 0.7, "typesafe/jev-1.14-20261001", 0.00002))

    def test_an_http_error_is_an_error(self):
        self.assertTrue(run.parse_jev(429, "rate limited")["error"].startswith("HTTP 429"))

    def test_a_choice_outside_its_probabilities_is_malformed(self):
        r = run.parse_jev(*reply("maybe", {"supports": 1.0}))
        self.assertTrue(r["error"].startswith("malformed"), r)


class AskTest(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out)
        os.environ["OPENROUTER_API_KEY"], os.environ["JEV_MODEL"] = KEY, "typesafe/jev-1.14"
        self.addCleanup(os.environ.pop, "OPENROUTER_API_KEY")
        self.addCleanup(os.environ.pop, "JEV_MODEL")

    def records(self):
        return list(run.recorded(os.path.join(self.out, "jev.jsonl")).values())

    def test_an_error_is_recorded_with_no_recommendation(self):
        run.ask([CASE], "set", "jev", self.out, send=lambda key, body: (None, "TimeoutError: timed out"))
        [rec] = self.records()
        self.assertEqual((rec["recommendation"], rec["answer"]), (None, None))
        self.assertIn("TimeoutError", rec["error"])

    def test_a_recorded_case_is_skipped_and_an_error_retried_only_when_asked(self):
        calls = []
        def send(key, body):
            calls.append(body["state"])
            return (500, "down") if len(calls) == 1 else reply("supports", {"supports": 0.95})
        run.ask([CASE], "set", "jev", self.out, send=send)
        run.ask([CASE], "set", "jev", self.out, send=send)
        self.assertEqual(len(calls), 1)
        run.ask([CASE], "set", "jev", self.out, retry_errors=True, send=send)
        self.assertEqual((len(calls), self.records()[0]["recommendation"]), (2, "pass"))

    def test_the_record_names_the_call_and_never_holds_the_key(self):
        sent = []
        run.ask([CASE], "set", "jev", self.out, send=lambda key, body: sent.append(key) or reply(
            "supports", {"supports": 0.95}))
        with open(os.path.join(self.out, "jev.jsonl"), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(sent, [KEY])
        self.assertNotIn(KEY, text)
        rec = json.loads(text)
        for field in ("commit", "bundle_sha256", "question", "served", "answer", "probability",
                      "recommendation", "at"):
            self.assertIsNotNone(rec[field], field)

    def test_the_floor_answers_supports_and_calls_nothing(self):
        run.ask([CASE], "set", "floor", self.out, send=lambda key, body: self.fail("called"))
        [rec] = run.recorded(os.path.join(self.out, "floor.jsonl")).values()
        self.assertEqual((rec["answer"], rec["recommendation"]), ("supports", "pass"))


class IngestTest(unittest.TestCase):
    def test_an_abstention_is_a_flag_and_a_bad_answer_an_error(self):
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out)
        cases = [CASE, dict(CASE, id="R02")]
        run.ingest(cases, "set", {"R01": {"abstain": True}, "R02": {"answer": "yes"}}, out)
        recs = run.recorded(os.path.join(out, "opus.jsonl"))
        self.assertEqual((recs["R01"]["recommendation"], recs["R01"]["abstained"]), ("flag", True))
        self.assertEqual(recs["R02"]["recommendation"], None)
        self.assertTrue(recs["R02"]["error"].startswith("malformed"))


if __name__ == "__main__":
    unittest.main()
