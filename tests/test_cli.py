"""The command line, run as a user runs it."""
import json
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

    def test_stopwords_leave_the_top_list_and_only_it(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"The cat and the dog, a cat\n")
            r = run("--stopwords", "--top", "3", a)
        self.assertEqual((r.returncode, r.stdout), (0, f" 1  7 27 {a}\n2 cat\n1 dog\n"))

    def test_stopwords_without_top_prints_the_counts_alone(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"The cat and the dog, a cat\n")
            r = run("--stopwords", a)
        self.assertEqual((r.returncode, r.stdout), (0, f" 1  7 27 {a}\n"))

    def test_json_prints_the_counts_as_one_object(self):
        r = run_with_input(b"The cat and the dog, a cat\n", "--json", "--stopwords", "--top", "3")
        self.assertEqual((r.returncode, r.stdout),
                         (0, '{"files": [{"name": "-", "lines": 1, "words": 7, "characters": 27}], '
                             '"top": [{"word": "cat", "count": 2}, {"word": "dog", "count": 1}]}\n'))

    def test_json_matches_the_plain_output(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"the cat\n")
            b = write(d, "b.txt", b"the dog sat\n")
            r_json = run("--json", "--top", "2", a, b)
            r_plain = run("--top", "2", a, b)
        self.assertEqual((r_json.returncode, r_plain.returncode), (0, 0))
        self.assertEqual(r_json.stdout.count("\n"), 1)
        # Plain rows: the two files, then the total, then the top words.
        lines = r_plain.stdout.splitlines()
        files = []
        for line in lines[:2]:
            n, w, c, name = line.lstrip().split(None, 3)
            files.append({"name": name, "lines": int(n), "words": int(w), "characters": int(c)})
        n, w, c, _ = lines[2].lstrip().split(None, 3)
        total = {"lines": int(n), "words": int(w), "characters": int(c)}
        top = [{"word": word, "count": int(count)}
               for count, word in (line.split(None, 1) for line in lines[3:])]
        obj = json.loads(r_json.stdout)
        self.assertEqual(obj["files"], files)
        self.assertEqual(obj["total"], total)
        self.assertEqual(obj["top"], top)

    def test_json_leaves_out_a_file_that_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as d:
            a = write(d, "a.txt", b"one two three\n")
            missing = os.path.join(d, "missing.txt")
            r = run("--json", missing, a)
        self.assertEqual(r.returncode, 1)
        self.assertIn(missing, r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(json.loads(r.stdout),
                         {"files": [{"name": a, "lines": 1, "words": 3, "characters": 14}],
                          "total": {"lines": 1, "words": 3, "characters": 14}})


if __name__ == "__main__":
    unittest.main()
