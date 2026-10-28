# Day 03 — `--top N`, the most frequent words

**Phase:** 0 · **Depends on:** Day 1 · **Expected PRs:** 3 (this spec change, Track A, the close)

## Goal
`python -m wordtally --top N FILE...` prints, after the count lines and the total, the N most
frequent words of the files counted, case folded, so that Phase 0's "done when" holds.

## In scope
- An option parser (`argparse`) for `--top N` and one or more files. Without `--top` the output is
  Day 1's, byte for byte.
- With `--top N`: after the last count line (the total, when there is one), N lines, each
  "COUNT WORD": the count, one space, the word. No padding, no header (H1.2).
- The words are `words()`, the plan's word rule, lowercased with `str.lower()`, summed over every
  file that was read; a file that cannot be read adds none.
- Order: count descending, then the word in ascending code-point order for equal counts (H1.2).
  Fewer than N distinct words prints them all.
- N that is not a whole number of at least 1 is a usage error: exit 2, nothing on stdout, a line
  containing "usage:" on stderr.

## Out of scope
- Standard input, and whether it counts in the total — Day 2, decided at this day's stop (H3.1).
- `--stopwords` — Day 4. `--json` — Day 5.
- Any change to the word rule: `tests/contract/` is frozen. "'quoted'" stays one word, quotes
  and all, in the top list too.

## Tracks

| Track | Owner | Work |
|---|---|---|
| A | implementer | `wordtally/__main__.py`: `argparse`, `--top`; `wordtally/count.py`: nothing, or a helper beside `words`; `tests/test_cli.py`: the three tests C3.1–C3.3 name, added, no Day 1 test edited |

No Track 0: the two **hold** checks, C3.4 and C3.5, exist today, and their breaks are in this
spec-change PR.

## Acceptance criteria
The tests write their files as bytes in a temporary directory and pass full paths, as Day 1's
do; "a.txt" stands for that path.

- [ ] C3.1 **new** — the top words follow the total, case folded, over all files: with a.txt
      holding "the cat The dog" and a newline, and b.txt "the cat" and a newline,
      `python -m wordtally --top 3 a.txt b.txt` prints exactly " 1  4 16 a.txt",
      " 1  2  8 b.txt", " 2  6 24 total", "3 the", "2 cat", "1 dog", each with a newline, and
      exits 0. Test: `CliTest.test_top_lists_the_most_frequent_words_after_the_total`. Red today:
      "--top" and "3" are read as files, two "wordtally:" lines go to stderr, no word lines are
      printed, and it exits 1.
- [ ] C3.2 **new** — ties go alphabetically and N cuts the list: c.txt holding "b a b a c" and a
      newline, `python -m wordtally --top 2 c.txt` prints exactly " 1  5 10 c.txt", "2 a", "2 b",
      each with a newline, and exits 0. Test:
      `CliTest.test_top_breaks_ties_alphabetically_and_stops_at_n`. Red today: as C3.1.
- [ ] C3.3 **new** — N below 1 is a usage error: `python -m wordtally --top 0 a.txt` exits 2,
      prints nothing on stdout, and stderr contains "usage:". Test:
      `CliTest.test_top_below_one_is_a_usage_error`. Red today: it exits 1 and prints a.txt's
      line and a total on stdout.
- [ ] C3.4 **hold** — without `--top` the output is Day 1's: the 8 tests in `tests/test_cli.py`
      today pass, and none is edited: `git diff main -- tests/test_cli.py | grep -c '^-[^-]'`
      prints 0 (grep exits 1 when it does).
      broken: the column width in wordtally/__main__.py, one wider → AssertionError: Tuples differ: (0, '  1   3  13 C:\\Users\\HACKYO~1\\AppData\\[30 chars]t\n') != (0, ' 1  3 13 C:\\Users\\HACKYO~1\\AppData\\Loc[27 chars]t\n')
      broken: a line of test_no_file_is_a_usage_error edited in tests/test_cli.py → removed=1
      broken: a line only added to tests/test_cli.py, the near miss → removed=0
      (The near miss ran with the check inverted, so that "failed" means the grep counted 0: the
      diff's "---" header and its added line are not counted as removed.)
- [ ] C3.5 **hold** — the word rule is untouched: `python -m unittest tests.contract.test_word_rule`
      passes and `git diff --exit-code --stat main -- tests/contract/` prints nothing.
      broken: the apostrophe dropped from WORD in wordtally/count.py → AssertionError: Lists differ: ['don', 't', 'stop'] != ["don't", 'stop']
      broken: a contract test renamed in tests/contract/test_word_rule.py → 1 file changed, 1 insertion(+), 1 deletion(-)

## Verify
```bash
python -m unittest discover -s tests -t .    # Ran 16 tests, OK (5 contract, 11 CLI)
python -m unittest tests.contract.test_word_rule
git diff --exit-code --stat main -- tests/contract/
d=$(mktemp -d) && printf 'the cat The dog\n' > "$d/a.txt" && printf 'the cat\n' > "$d/b.txt" && python -m wordtally --top 3 "$d/a.txt" "$d/b.txt"
```

The last command, with the directory shown as D:

```text
 1  4 16 D/a.txt
 1  2  8 D/b.txt
 2  6 24 total
3 the
2 cat
1 dog
```

## Notes
- H1.2 is picked up here: the `--top` lines go after the total line, and ties are ordered by the
  word. Where standard input goes in the total is not this day's to decide (H3.1).
- Left to the rule, with no criterion of their own: `--top` with every file unreadable prints no
  word lines; `--top` larger than the distinct words prints them all (C3.2 shows the cut, not this).
- `argparse` changes what no Day 1 test covers, and that is accepted: a file named like an option
  ("-x") is an option error, `-h` prints help, and the usage text is argparse's (it still holds
  "usage:", so C1.8 stands until Day 2, H1.1). Track A rewords the comment in
  `wordtally/__main__.py` that says Day 3 decides where standard input goes: the stop does (H3.1).
- **Defect** — found: auditor · cause: spec · made: Day 03 · the first draft's C3.4 said
  "`git diff main -- tests/test_cli.py` removes no line", with no command whose output passes or
  fails. Now a `grep -c` that prints 0, broken both ways; fixed in this PR.
- **Defect** — found: self · cause: environment · made: Day 03 · the first run of C3.4's two
  breaks passed `bash` to `scripts/break.py`, which resolved to WSL's bash and never started
  ("execvpe(/bin/bash) failed"); `break.py` printed `broken:` lines for checks that never ran.
  Run again with Git Bash's full path before this PR opened.
- **Hand-off** H3.1 → the maintainer: `plan.md`'s Day 3 stop decides whether standard input
  counts as a file named `-` in the total or stands alone; the plan-auditor reports on it at the
  close, and Day 2's spec cites this ID with the choice.
