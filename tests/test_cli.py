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


def write(d, name, data):
    # Bytes, so that Windows writes no carriage return the test did not ask for.
    path = os.path.join(d, name)
    with open(path, "wb") as f:
        f.write(data)
    return path


class CliTest(unittest.TestCase):
    def test_one_file_prints_lines_words_and_characters(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one two three\n")
            r = run(a)
        self.assertEqual((r.returncode, r.stdout), (0, f" 1  3 14 {a}\n"))

    def test_two_files_print_a_total_line(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one two three\n")
            b = write(d, "b.txt", b"four\n")
            r = run(a, b)
        self.assertEqual((r.returncode, r.stdout),
                         (0, f" 1  3 14 {a}\n 1  1  5 {b}\n 2  4 19 total\n"))

    def test_a_last_line_with_no_newline_is_not_counted(self):
        with tempfile.TemporaryDirectory() as d:
            n = write(d, "n.txt", b"no newline")
            r = run(n)
        self.assertEqual((r.returncode, r.stdout), (0, f" 0  2 10 {n}\n"))

    def test_words_follow_the_word_rule_and_characters_are_not_bytes(self):
        data = "café e-mail\r\n".encode("utf-8")
        self.assertEqual(len(data), 14)
        with tempfile.TemporaryDirectory() as d:
            x = write(d, "x.txt", data)
            r = run(x)
        self.assertEqual((r.returncode, r.stdout), (0, f" 1  3 13 {x}\n"))

    def test_a_missing_file_is_reported_and_the_rest_counted(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one two three\n")
            missing = os.path.join(d, "missing.txt")
            r = run(a, missing)
        self.assertEqual((r.returncode, r.stdout),
                         (1, f" 1  3 14 {a}\n 1  3 14 total\n"))
        self.assertTrue(r.stderr.startswith(f"wordtally: {missing}:"))
        self.assertNotIn("Traceback", r.stderr)

    def test_a_file_that_is_not_utf8_is_reported_and_the_rest_counted(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one two three\n")
            bad = write(d, "bad.txt", b"\xff\n")
            r = run(a, bad)
        self.assertEqual((r.returncode, r.stdout),
                         (1, f" 1  3 14 {a}\n 1  3 14 total\n"))
        self.assertTrue(r.stderr.startswith(f"wordtally: {bad}:"))
        self.assertNotIn("Traceback", r.stderr)

    def test_when_every_file_fails_the_total_is_zeros(self):
        with tempfile.TemporaryDirectory() as d:
            missing = os.path.join(d, "missing.txt")
            gone = os.path.join(d, "gone.txt")
            r = run(missing, gone)
        self.assertEqual((r.returncode, r.stdout), (1, "0 0 0 total\n"))
        self.assertEqual(len([line for line in r.stderr.splitlines()
                              if line.startswith("wordtally:")]), 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_no_file_is_a_usage_error(self):
        r = run()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("usage:", r.stderr)


if __name__ == "__main__":
    unittest.main()
