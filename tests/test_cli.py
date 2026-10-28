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


def run_with_input(data, *args):
    # Bytes in and out, decoded here: a text-mode pipe on Windows adds a carriage return.
    r = subprocess.run([sys.executable, "-m", "wordtally", *args], cwd=ROOT,
                       capture_output=True, input=data)
    return subprocess.CompletedProcess(r.args, r.returncode,
                                       r.stdout.decode("utf-8").replace("\r\n", "\n"),
                                       r.stderr.decode("utf-8").replace("\r\n", "\n"))


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


    def test_top_lists_the_most_frequent_words_after_the_total(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"the cat The dog\n")
            b = write(d, "b.txt", b"the cat\n")
            r = run("--top", "3", a, b)
        self.assertEqual((r.returncode, r.stdout),
                         (0, f" 1  4 16 {a}\n 1  2  8 {b}\n 2  6 24 total\n"
                             "3 the\n2 cat\n1 dog\n"))

    def test_top_breaks_ties_alphabetically_and_stops_at_n(self):
        with tempfile.TemporaryDirectory() as d:
            c = write(d, "c.txt", b"b a b a c\n")
            r = run("--top", "2", c)
        self.assertEqual((r.returncode, r.stdout),
                         (0, f" 1  5 10 {c}\n2 a\n2 b\n"))

    def test_top_below_one_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one\n")
            r = run("--top", "0", a)
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("usage:", r.stderr)

    def test_no_file_reads_standard_input(self):
        r = run_with_input(b"the cat\nsat\n")
        self.assertEqual((r.returncode, r.stdout), (0, " 2  3 12 -\n"))

    def test_a_dash_reads_standard_input_and_counts_in_the_total(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"the cat\n")
            r = run_with_input(b"sat\n", a, "-")
        self.assertEqual((r.returncode, r.stdout),
                         (0, f" 1  2  8 {a}\n 1  1  4 -\n 2  3 12 total\n"))

    def test_standard_input_is_utf8_with_its_carriage_returns(self):
        r = run_with_input(b"a\r\n" + "éé\n".encode("utf-8"), "-")
        self.assertEqual((r.returncode, r.stdout), (0, "2 1 6 -\n"))


if __name__ == "__main__":
    unittest.main()
