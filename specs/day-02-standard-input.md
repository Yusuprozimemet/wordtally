# Day 02 — standard input, a file named `-`

**Phase:** 1 · **Depends on:** Day 3, and its stop (H3.1) · **Expected PRs:** 3 (this spec change,
Track A, the close)

## Goal
`python -m wordtally` with no file named, or with `-` among the names, counts what standard input
holds, as a file named `-`, so that a pipe can feed Phase 1's "done when".

## In scope
- The name `-` reads standard input. With no name given, wordtally reads `["-"]` (the Day 3 stop,
  H3.1): one line, named `-`, and no total.
- `-` is one name among the rest: a total line when more than one name is given, `-` counting as
  one. Its words go into the `--top` tally as a file's do.
- Standard input is read as bytes and decoded as UTF-8, as files are: no newline is translated, so
  a carriage return counts as a character. Input that is not UTF-8 is reported as a file's is, with
  the name `-`: "wordtally: -: ..." on stderr, and exit 1.
- `-` named twice reads standard input once: the second read finds it empty and prints zeros,
  as `wc` does. Order of the names is kept.
- C1.8's usage error expires (H1.1): `test_no_file_is_a_usage_error` is removed.

## Out of scope
- `--stopwords` — Day 4. `--json` — Day 5.
- Any change to the word rule: `tests/contract/` is frozen.

## Tracks

| Track | Owner | Work |
|---|---|---|
| A | implementer | `wordtally/__main__.py`: `nargs="*"` with the default `["-"]`, `-` read from `sys.stdin.buffer` and decoded as UTF-8 down the files' error path, the comment above the total reworded to cite the stop's decision; `tests/test_cli.py`: `test_no_file_is_a_usage_error` removed, a new helper beside `run()` that feeds standard input as bytes, the three tests C2.1–C2.3 name added with it; `run()` and every other test unedited |

No Track 0: the hold, C2.4, exists today, and its breaks are in this spec-change PR.

## Acceptance criteria
The tests feed standard input as bytes (`input=` with no `text=True`), since a text-mode pipe on
Windows writes a carriage return the test did not ask for. Files are written as Day 1's are.

- [x] C2.1 **new** — no name reads standard input: with "the cat" and a newline, then "sat" and a
      newline, on standard input, `python -m wordtally` prints exactly " 2  3 12 -" and a newline,
      and exits 0. Test: `CliTest.test_no_file_reads_standard_input`. Red today: it exits 2 and
      prints nothing on stdout, "usage:" on stderr.
      Evidence: `CliTest.test_no_file_reads_standard_input` (#12), seen red first on `main`'s code.
      broken: the default of no name emptied in wordtally/__main__.py → AssertionError: Tuples differ: (0, '') != (0, ' 2  3 12 -\n') (#12)
- [x] C2.2 **new** — `-` is one name among the rest: with a.txt holding "the cat" and a newline,
      and "sat" and a newline on standard input, `python -m wordtally a.txt -` prints exactly
      " 1  2  8 a.txt", " 1  1  4 -", " 2  3 12 total", each with a newline, and exits 0. Test:
      `CliTest.test_a_dash_reads_standard_input_and_counts_in_the_total`. Red today:
      "wordtally: -: No such file or directory" on stderr, a.txt's line and a total of a.txt's
      counts alone, and exit 1.
      Evidence: `CliTest.test_a_dash_reads_standard_input_and_counts_in_the_total` (#12), seen red first on `main`'s code.
      broken: the name - not recognised in read() → AssertionError: Tuples differ: (1, '1 2 8 C:\Users\HACKYO~1\AppData\L[42 chars]l\n') != (0, ' 1  2  8 C:\Users\HACKYO~1\AppData[60 chars]l\n') (#12)
- [x] C2.3 **new** — standard input is UTF-8 bytes, its newlines untranslated: with the bytes
      "a", carriage return, newline, then "éé" in UTF-8 and a newline, on standard input,
      `python -m wordtally -` prints exactly "2 1 6 -" and a newline, and exits 0. On Windows a
      text-mode `sys.stdin` read gives 7 characters (cp1252, the carriage return dropped), so
      the test catches it; on CI's Linux, `sys.stdin` is UTF-8 and translates no newline, so a
      text-mode read also gives 6 there and only a Windows run tells the two apart. Test:
      `CliTest.test_standard_input_is_utf8_with_its_carriage_returns`. Red today:
      "wordtally: -: No such file or directory" on stderr, nothing on stdout, and exit 1.
      Evidence: `CliTest.test_standard_input_is_utf8_with_its_carriage_returns` (#12), seen red first on `main`'s code.
      broken: standard input read in text mode → AssertionError: Tuples differ: (0, '2 1 7 -\n') != (0, '2 1 6 -\n') (#12)
- [x] C2.4 **hold** — the rest of Day 1's and Day 3's behaviour stands: the suite passes, and no
      line of `tests/test_cli.py` is removed or edited but `test_no_file_is_a_usage_error`'s four
      (lines 83–86 at `46b9423`, `main` before this day; naming `main` would compare Track A's
      file with itself once it merges):
      `diff --strip-trailing-cr <(git show 46b9423:tests/test_cli.py | sed 83,86d) tests/test_cli.py | grep -c '^<'`
      prints 0 (grep exits 1 when it does). A count of removed lines would not do: two of the
      four lines are also in C3.3's test.
      broken: a line of test_top_below_one_is_a_usage_error edited in tests/test_cli.py → removed=1
      broken: the run line of test_no_file_is_a_usage_error emptied, the near miss → removed=0
      broken: the total line's name in wordtally/__main__.py → AssertionError: Tuples differ: (0, '[99 chars]1\\AppData\\Local\\Temp\\tmp_awyqq9m\\b.txt\n 2  4 19 Total\n') != (0, '[99 chars]1\\AppData\\Local\\Temp\\tmp_awyqq9m\\b.txt\n 2  4 19 total\n')
      (The near miss passes by design: a line of the test that may go is not counted.)
      Evidence: after #12, the suite runs 18 tests, OK, and the diff command prints 0 on `main`
      (`33b73cf`); broken in #11.

## Verify
```bash
python -m unittest discover -s tests -t .    # Ran 18 tests, OK (5 contract, 13 CLI)
diff --strip-trailing-cr <(git show 46b9423:tests/test_cli.py | sed 83,86d) tests/test_cli.py | grep -c '^<'    # 0
printf 'the cat\nsat\n' | python -m wordtally
```

The last command prints:

```text
 2  3 12 -
```

## Notes
- H1.1 and H3.1 are picked up here: no name means `["-"]`, `-` prints as its name, and it counts
  as one name in the total (`plan.md`, Course corrections).
- Left to the rule, with no criterion of their own: `-` named twice (In scope); standard input
  that is not UTF-8 goes down the same path as a file that is not (C1.6's test covers that path
  for files).
- **Defect** — found: spec-change PR · cause: spec · made: Day 02 · the first draft's C2.4 was a hold that
  failed today: `grep -c '^-[^-]'` "prints 4" is true only after Track A, and a count of removed
  lines cannot tell the expiring test's lines from C3.3's. Now a diff against `main`'s file with
  that test cut out; fixed in this PR.
- **Defect** — found: spec-change PR · cause: environment · made: Day 02 · C2.4's first run diffed `git show`'s
  LF lines against the CRLF working tree and counted 109 removed lines; `--strip-trailing-cr`
  added before any break ran.
- **Defect** — found: auditor · cause: spec · made: Day 02 · the tests had to feed bytes but
  `run()` hard-codes `text=True`, and editing it turns C2.4 red. Now a separate helper, `run()`
  unedited; fixed in this PR.
- **Defect** — found: auditor · cause: spec · made: Day 02 · C2.3 claimed a text-mode read drops
  the carriage return on CI's Linux, where CPython's `sys.stdin` translates no newline. Now: the
  check bites only on Windows; fixed in this PR.
- **Defect** — found: auditor · cause: spec · made: Day 02 · C2.4 named `main` as its base, which
  ticks itself once Track A merges, as Day 3's C3.4 did. Now `46b9423`; fixed in this PR.
- C2.4's breaks were run with `main` as the base, before the third fix; `main` was `46b9423`
  then, so the same commands.
- The plan-auditor ran on Phase 1 before this spec (0 blocking, 4 for Day 2: C1.8's expiry, tests
  feeding standard input as bytes, `sys.stdin.buffer` over text mode, `-` twice and mixed). All
  four are in this spec. Its note that the tests' `run()` inherits the parent's standard input
  matters only to a test that names no file: those added here pass `input=`.
- **Defect** — found: self · cause: implementation · made: Day 02 · the implementer's first draft
  of `run_with_input()` decoded the child's output but left its `\r\n` line endings, so all three
  new tests failed on Windows, where `print` writes a carriage return. Its own run of the tests
  caught it, and it fixed the helper before reporting; it never reached #12.
- **Rewrite** — Track A: none. The implementer's code (#12) was taken as written, after review.
- Track A's three breaks, one per new criterion, are recorded under the criterion whose test
  they turned red. All three new tests were seen red first on `main`'s code (#12: "Ran 18 tests",
  "FAILED (failures=3)"). C2.4's breaks are #11's; this close ran none.
- C2.3's break bites only on Windows, as the criterion says: CI's Linux run passes a text-mode
  read too, so that criterion is guarded by a local run, not by the "Unit tests" check.
- `-` named twice, left to the rule, was run by hand at this close on `main` (`33b73cf`):
  `printf 'x\n' | python -m wordtally - -` prints "1 1 2 -", "0 0 0 -", "1 1 2 total", as In
  scope says.
- Day 2 ran after Day 3, as `plan.md`'s Day 3 stop decided (#10); its premises were checked
  against Day 3's merged code, not Day 1's.
- The spec-auditor's three findings, one Defect line in #11, are split into three at this close:
  `specs/README.md` asks for one line per problem.
- Two tags changed at this close, after the blind rater's first pass over the four lines #11 and
  this close had written (`relabel.py compare`: stage 3 of 4, cause 3 of 4, made 4 of 4). The
  C2.4 draft defect goes from "found: self" to "found: spec-change PR", as the blind
  rater read it: it was caught in #11 before any code. The CRLF diff defect goes the same way by
  the same rule, though the rater agreed with "self" there; its cause stays "environment", where
  the rater read "spec" with low confidence, since the command was right and the CRLF working
  tree broke it, as Day 3's WSL `bash` defect was tagged. This is the third day running that
  "found: self" was written for a spec-change PR catch; Days 1 and 3 made the same correction.
  A second blind pass, over the six lines after the split and the changes: stage 5 of 6, cause 5
  of 6, made 6 of 6; the two left are the CRLF defect's stage and cause, both low confidence, and
  both kept as tagged.
