# Day 01 — Lines, words and characters per file

**Phase:** 0 · **Depends on:** none (the seed, df0c205) · **Expected PRs:** 3 (this spec change,
Track A, the close)

## Goal
`python -m wordtally FILE...` prints each file's lines, words and characters in columns, as `wc`
lays them out, and a total line when two or more files are named.

## In scope
- Three counts per file, in this order: lines, words, characters, then the file's name.
  - **Lines** are the number of newline characters, as `wc -l` counts them: a last line with no
    newline adds none.
  - **Words** are `count_words`, the plan's word rule, not the whitespace words of `wc`: "e-mail"
    is two words here and one in `wc`. "As `wc` prints them" means the layout only.
  - **Characters** are the characters of the text decoded as UTF-8, as `wc -m` counts them, not
    bytes (`wc -c`). The file is read with `newline=""`, so a carriage return counts as one.
- The layout: every number right-aligned to the width of the widest number on any line printed
  (the total included), the numbers separated by one space, then one space and the name as given
  on the command line. This is close to GNU `wc`, which sizes its columns by the files' bytes
  instead; the fixed width of 8 in BSD `wc` is not followed.
- A last line named "total", with the sums, when two or more files are named on the command line.
- A file that cannot be read (any `OSError`, or a `UnicodeDecodeError`): one line on stderr,
  "wordtally: PATH: REASON", no line on stdout, the other files still counted, exit 1. REASON is
  free text; the tests check the line up to the second colon. The total sums the files counted.

## Out of scope
- Standard input, and whether it counts in the total — Day 2, after Day 3's stop decides it.
- `--top N` and an option parser — Day 3.
- `--stopwords` — Day 4. `--json` — Day 5, whose keys follow this day's three names.
- Any change to the word rule: `tests/contract/` is frozen.

## Tracks

| Track | Owner | Work |
|---|---|---|
| A | implementer | `wordtally/count.py`: a `counts` function giving lines, words and characters; `wordtally/__main__.py`: the layout, the total and the read errors; `tests/test_cli.py`: the tests C1.1–C1.7 name, replacing `test_each_file_prints_its_word_count_and_name` |

No Track 0: the two **hold** checks, C1.8 and C1.9, are checks that exist today, and their breaks
are in this spec-change PR.

## Acceptance criteria
The tests write the files in a temporary directory, as bytes (mode "wb"), so that Windows writes no
carriage return the criterion did not ask for, and pass each file by its full path. "a.txt" below
stands for that path, as printed. Verify shows the exact output, spaces included.

- [ ] C1.1 **new** — one file prints one line: with a.txt holding "one two three" and a newline,
      `python -m wordtally a.txt` prints exactly " 1  3 14 a.txt" and a newline, and exits 0.
      Test: `CliTest.test_one_file_prints_lines_words_and_characters`. Red today: it prints
      "3 a.txt".
- [ ] C1.2 **new** — two files print a total: with b.txt holding "four" and a newline,
      `python -m wordtally a.txt b.txt` prints exactly " 1  3 14 a.txt", " 1  1  5 b.txt" and
      " 2  4 19 total", each with a newline, and exits 0. Test:
      `CliTest.test_two_files_print_a_total_line`, which replaces
      `test_each_file_prints_its_word_count_and_name`. Red today: it prints "3 a.txt" and
      "1 b.txt", and no total.
- [ ] C1.3 **new** — lines are newlines: n.txt holding "no newline", with no newline at the end,
      prints " 0  2 10 n.txt". Test: `CliTest.test_a_last_line_with_no_newline_is_not_counted`.
      Red today: it prints "2 n.txt".
- [ ] C1.4 **new** — words follow the word rule, characters are decoded, and a carriage return
      counts: x.txt holding "café e-mail" and a CRLF (14 bytes in UTF-8) prints
      " 1  3 13 x.txt", where `wc` counts 2 words and `wc -c` 14 bytes (`wc -m` agrees on 13
      characters in a UTF-8 locale). Test:
      `CliTest.test_words_follow_the_word_rule_and_characters_are_not_bytes`. Red today: it
      prints "3 x.txt".
- [ ] C1.5 **new** — a missing file is reported and the rest counted:
      `python -m wordtally a.txt missing.txt` prints " 1  3 14 a.txt" and " 1  3 14 total" on
      stdout, a line starting "wordtally: missing.txt:" on stderr and no traceback, and exits 1.
      Test: `CliTest.test_a_missing_file_is_reported_and_the_rest_counted`. Red today: stdout is
      "3 a.txt", stderr is a `FileNotFoundError` traceback.
- [ ] C1.6 **new** — a file that is not UTF-8 is reported the same way: bad.txt holding the byte
      0xff and a newline, named after a.txt, gives the same stdout as C1.5, a line starting
      "wordtally: bad.txt:" on stderr, no traceback, and exit 1. Test:
      `CliTest.test_a_file_that_is_not_utf8_is_reported_and_the_rest_counted`. Red today:
      stderr is a `UnicodeDecodeError` traceback.
- [ ] C1.7 **new** — when every named file fails, the total is zeros:
      `python -m wordtally missing.txt gone.txt` prints exactly "0 0 0 total" and a newline on
      stdout, two "wordtally:" lines on stderr and no traceback, and exits 1. Test:
      `CliTest.test_when_every_file_fails_the_total_is_zeros`. Red today: stdout is empty, stderr
      is a `FileNotFoundError` traceback.
- [ ] C1.8 **hold** — no file named is a usage error: `python -m wordtally` prints nothing on
      stdout, "usage:" on stderr, and exits 2. Test: `CliTest.test_no_file_is_a_usage_error`,
      unedited. It expires on Day 2 (H1.1).
      broken: the no-file check in `wordtally/__main__.py` (if not paths: → if False:) → AssertionError: Tuples differ: (0, '') != (2, '')
- [ ] C1.9 **hold** — the word rule stands: `git diff --exit-code --stat main -- tests/contract/`
      prints nothing and exits 0, and `python -m unittest tests.contract.test_word_rule` runs 5
      tests, OK.
      broken: `WORD` in `wordtally/count.py` without the apostrophe → AssertionError: Lists differ: ['don', 't', 'stop'] != ["don't", 'stop']
      broken: one expected value in `tests/contract/test_word_rule.py` (66 → 67) → 1 file changed, 1 insertion(+), 1 deletion(-)

## Verify
```bash
python -m unittest discover -s tests -t .    # Ran 13 tests, OK (5 contract, 8 CLI)
python -m unittest tests.contract.test_word_rule
git diff --exit-code --stat main -- tests/contract/
d=$(mktemp -d) && printf 'one two three\n' > "$d/a.txt" && printf 'four\n' > "$d/b.txt" && python -m wordtally "$d/a.txt" "$d/b.txt"
```

The last command, with the directory shown as D:

```text
 1  3 14 D/a.txt
 1  1  5 D/b.txt
 2  4 19 total
```

## Notes
- The total line appears when two or more files are named, not when two or more are counted, as
  in `wc`: a.txt and missing.txt print one file's line and a total. The condition lives in one
  place in `wordtally/__main__.py`, so Day 3's stop can decide where standard input goes (H1.2).
- The frozen rule turns "café" into "caf" and keeps a word's leading and trailing apostrophes
  ("'quoted'" is one word, quotes and all). That is the contract, not a defect, and Day 3's most
  frequent words will show it (plan-auditor, finding 10).
- Left to the rule, with no criterion of their own: an empty file prints "0 0 0" and its name; a
  file named twice is counted twice, in the total too, as in `wc`.
- **Defect** — found: auditor · cause: spec · made: none · `plan.md`'s Day 1 line, "as `wc` prints
  them", left open whether words and characters follow `wc` (whitespace words, bytes) or the plan's
  word rule and decoded characters, and how lines, the widths, read errors and the total are
  counted; the plan-auditor found six readings that differ on today's code. Settled in this spec,
  in this PR.
- **Defect** — found: auditor · cause: spec · made: none · the first draft had the tests write
  their files in text mode, as `test_each_file_prints_its_word_count_and_name` does; on Windows
  that writes CRLF, so C1.1–C1.5 would have failed locally and passed on CI's Linux. The spec now
  says bytes; fixed in this PR.
- **Defect** — found: auditor · cause: spec · made: none · the first draft's C1.4 said GNU `wc`
  prints 14 characters for x.txt; `wc -m` prints 13, only bytes are 14. Fixed in this PR.
- **Defect** — found: self · cause: process · made: none · the first draft recorded C1.9's break
  as "FAILED (failures=1)" before running it; `scripts/break.py` reported the assertion line, now
  recorded. Fixed in this PR, before the spec-auditor ran.
- **Hand-off** H1.1 → Day 2: C1.8's usage error, and `test_no_file_is_a_usage_error` with it,
  expires when no file named means standard input.
- **Hand-off** H1.2 → Day 3: the stop decides whether standard input counts in the total; Day 3's
  spec cites this and says where the `--top` lines go relative to the total line, and how ties
  are ordered.
