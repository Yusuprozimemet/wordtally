import importlib.util
import json
import os
import re
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, os.pardir, "scripts", "token-usage.py")
spec = importlib.util.spec_from_file_location("token_usage", SCRIPT)
token_usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(token_usage)


def native(path):
    # The test builds its files with its own \\?\ prefix, not the script's, so it runs on main's code too.
    return "\\\\?\\" + path if os.name == "nt" else path


def reply(n):
    return json.dumps({"type": "assistant", "timestamp": "2026-10-29T10:00:00Z", "gitBranch": "main",
                       "requestId": f"r{n}", "message": {"id": f"m{n}", "model": "claude-opus-5-5",
                                                         "usage": {"output_tokens": n}}}) + "\n"


class TokenUsageTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, native(self.root))
        name = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.join(HERE, os.pardir)))
        self.project = os.path.join(self.root, name)

    def write(self, path, text):
        os.makedirs(native(os.path.dirname(path)), exist_ok=True)
        with open(native(path), "w", encoding="utf-8") as f:
            f.write(text)

    def test_transcript_past_max_path_is_counted(self):
        # A subagent's transcript in a folder past 260 characters, beside a session at a short path.
        self.write(os.path.join(self.project, "short.jsonl"), reply(3))
        folder = os.path.join(self.project, "s" * 200, "subagents")
        self.write(os.path.join(folder, "agent-" + "a" * 100 + ".jsonl"), reply(7))
        self.write(os.path.join(folder, "agent-" + "a" * 100 + ".meta.json"), '{"agentType": "implementer"}')
        self.assertGreater(len(folder), 260)
        totals = token_usage.count(token_usage.transcripts(self.root))
        self.assertEqual({who: t["output"] for (_, _, _, who), t in totals.items()},
                         {"main": 3, "implementer": 7})


if __name__ == "__main__":
    unittest.main()
