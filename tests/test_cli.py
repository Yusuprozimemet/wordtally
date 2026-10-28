"""The command line, run as a user runs it."""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run([sys.executable, "-m", "wordtally", *args], cwd=ROOT,
                          capture_output=True, text=True)


class CliTest(unittest.TestCase):
    def test_each_file_prints_its_word_count_and_name(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.txt"), os.path.join(d, "b.txt")
            with open(a, "w", encoding="utf-8") as f:
                f.write("one two three\n")
            with open(b, "w", encoding="utf-8") as f:
                f.write("four\n")
            r = run(a, b)
        self.assertEqual((r.returncode, r.stdout), (0, f"3 {a}\n1 {b}\n"))

    def test_no_file_is_a_usage_error(self):
        r = run()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("usage:", r.stderr)


if __name__ == "__main__":
    unittest.main()
