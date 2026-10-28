# Day 04 — `--stopwords`, common words out of the top list

**Phase:** 1 · **Depends on:** Day 2 · **Expected PRs:** 3 (this spec change, Track A, the close)

## Goal
`python -m wordtally --stopwords --top N FILE...` leaves the words of a built-in English list out
of the top list, and changes nothing else, as `plan.md`'s Day 3 stop decided: a flag, filtering
only the `--top` tally.

## In scope
- `--stopwords`, a flag that takes no value. Without it the output is Day 3's and Day 2's, byte
  for byte.
- The list is `wordtally/stopwords.txt`: one lowercase word per line, English only, read as UTF-8
  from beside the package's code. It holds at least "a", "and" and "the". A line's carriage return
  is not part of its word: the working tree here is CRLF.
- With `--stopwords`, a word goes into the `--top` tally only when its lowercased form is not in
  the list. Lines, words and characters are counted as before, the stopwords included.
- `--stopwords` without `--top` is accepted and changes nothing.

## Out of scope
- A list given on the command line, or any language but English (`plan.md`, What we are not doing).
- `--json` — Day 5.
- Any change to the word rule: `tests/contract/` is frozen. "'the'", quotes and all, is not the
  stopword "the".

## Tracks

| Track | Owner | Work |
|---|---|---|
| A | implementer | `wordtally/stopwords.txt`: the list, new; `wordtally/__main__.py`: `--stopwords`, the list read, the tally filtered; `tests/test_cli.py`: the two tests C4.1 and C4.2 name, added, no other test edited |

No Track 0: the two **hold** checks, C4.3 and C4.4, exist today, and their breaks are in this
spec-change PR.

## Acceptance criteria
The tests write their files as bytes in a temporary directory and pass full paths, as Day 1's
do; "a.txt" stands for that path. a.txt holds "The cat and the dog, a cat" and a newline.

- [x] C4.1 **new** — stopwords leave the top list, and only it: `python -m wordtally --stopwords
      --top 3 a.txt` prints exactly " 1  7 27 a.txt", "2 cat", "1 dog", each with a newline, and
      exits 0. Without `--stopwords` the same file's top 3 is "2 cat", "2 the", "1 a". Test:
      `CliTest.test_stopwords_leave_the_top_list_and_only_it`. Red today: exit 2, nothing on
      stdout, "unrecognized arguments: --stopwords" on stderr. The list is the file: with "the"
      deleted from `wordtally/stopwords.txt`, the test fails with "2 the" in the output.
      Evidence: `CliTest.test_stopwords_leave_the_top_list_and_only_it` (#15), seen red on
      `e44ae6a`'s code at this close: "Tuples differ: (2, '') != (0, ...)".
      broken: "the" deleted from wordtally/stopwords.txt → AssertionError: Tuples differ: (0, '[32 chars]pData\Local\Temp\tmpf0ql2_cq\a.txt\n2 cat\n2 the\n1 dog\n') != (0, '[32 chars]pData\Local\Temp\tmpf0ql2_cq\a.txt\n2 cat\n1 dog\n') (#15)
      broken: the tally left unfiltered in wordtally/__main__.py → AssertionError: Tuples differ: (0, '[30 chars]AppData\Local\Temp\tmpk5ell9ro\a.txt\n2 cat\n2 the\n1 a\n') != (0, '[30 chars]AppData\Local\Temp\tmpk5ell9ro\a.txt\n2 cat\n1 dog\n') (#15)
- [x] C4.2 **new** — `--stopwords` without `--top` changes nothing: `python -m wordtally
      --stopwords a.txt` prints exactly " 1  7 27 a.txt" and a newline, and exits 0. Test:
      `CliTest.test_stopwords_without_top_prints_the_counts_alone`. Red today: as C4.1.
      Evidence: `CliTest.test_stopwords_without_top_prints_the_counts_alone` (#15), seen red on
      `e44ae6a`'s code at this close: "Tuples differ: (2, '') != (0, ...)".
      broken: --stopwords made to take a value in wordtally/__main__.py → AssertionError: Tuples differ: (1, '') != (0, ' 1  7 27 C:\Users\HACKYO~1\AppData\Local\Temp\tmp570dee_n\a.txt\n') (#15)
- [x] C4.3 **hold** — Days 1–3's behaviour stands: the 18 tests today pass, and none is edited:
      `git diff e44ae6a -- tests/test_cli.py | grep -c '^-[^-]'` prints 0 (grep exits 1 when it
      does). `e44ae6a` is `main` before this day; naming `main` would compare Track A's file with
      itself once it merges.
      broken: a line of test_top_below_one_is_a_usage_error edited in tests/test_cli.py → removed=1
      broken: a line only added to tests/test_cli.py, the near miss → removed=0
      broken: the total line's name in wordtally/__main__.py → AssertionError: Tuples differ: (0, '[99 chars]1\\AppData\\Local\\Temp\\tmpkgktw94n\\b.txt\n 2  4 19 Total\n') != (0, '[99 chars]1\\AppData\\Local\\Temp\\tmpkgktw94n\\b.txt\n 2  4 19 total\n')
      (The near miss ran with the check inverted, so that "failed" means the grep counted 0.)
      Evidence: after #15, the suite runs 20 tests, OK, and the diff command prints 0 on `main`
      (`1f99563`); broken in #14.
- [x] C4.4 **hold** — the word rule is untouched: `python -m unittest tests.contract.test_word_rule`
      passes and `git diff --exit-code --stat e44ae6a -- tests/contract/` prints nothing.
      broken: a space added to a line of tests/contract/test_word_rule.py → 1 file changed, 1 insertion(+), 1 deletion(-)
      broken: words() split on whitespace in wordtally/count.py → AssertionError: Lists differ: ['Hello,', 'world!'] != ['Hello', 'world']
      Evidence: on `main` (`1f99563`), `tests.contract.test_word_rule` gives OK and the diff
      prints nothing, exit 0; broken in #14.

## Verify
```bash
python -m unittest discover -s tests -t .    # Ran 20 tests, OK (5 contract, 15 CLI)
git diff e44ae6a -- tests/test_cli.py | grep -c '^-[^-]'    # 0
git diff --exit-code --stat e44ae6a -- tests/contract/      # nothing, exit 0
printf 'The cat and the dog, a cat\n' | python -m wordtally --stopwords --top 3
```

The last command prints:

```text
 1  7 27 -
2 cat
1 dog
```

## Notes
- No hand-off names Day 4. The Day 3 stop's decision (`plan.md`, Course corrections) is the
  premise: a flag, the `--top` tally only.
- The list's carriage returns bite only on Windows: the checkout there is CRLF, CI's Linux
  checkout LF. A read that keeps "the\r" fails C4.1 locally and passes CI's "Unit tests", as
  Day 2's C2.3 did.
- The spec-auditor ran before this PR: ready, nothing blocking, 3 notes. One is taken (the
  carriage-return line above); the other two need no change: `'^-[^-]'` misses a removed blank
  line, harmless for "no test edited", and no hand-off names Day 4.
- C4.3's and C4.4's breaks ran through `scripts/break.py` with Git Bash named by its full path,
  not `bash`, which Day 3 found resolves to WSL's.
- **Defect** — found: spec-change PR · cause: process · made: Day 04 · the near miss's first
  run, in this PR before any code, reported git's CRLF warning as its line, since the check's
  `git diff` ran without `core.safecrlf=false`; rerun with it, and the line above is the rerun's.
- `scripts/spec-drift.py` still prints "Day 03 is done: stop and evaluate before going on": it
  lifts a stop only on a "Course correction after Phase 0" section, and `plan.md` records the
  stop's decisions under "Course corrections" instead. Day 2 ran under the same message.
- **Defect** — found: review · cause: process · made: Day 04 · the implementer's report for
  Track A said `wordtally/stopwords.txt` holds 40 words; it holds 45. Caught in review of its
  diff and corrected in #15's description; the code needed no change.
- **Defect** — found: close · cause: process · made: Day 04 · #15 recorded three breaks but not
  that C4.1's and C4.2's tests were seen red on the code before the day, as Day 2's #12 did. Run
  at this close: with #15's `tests/test_cli.py` over `e44ae6a`'s code, both fail, "Ran 2 tests",
  "FAILED (failures=2)", exit 2 and nothing on stdout, as "Red today" says.
- **Rewrite** — Track A: none. The implementer's code (#15) was taken as written, after review.
- Track A's three breaks are recorded under the criterion whose test they turned red: two under
  C4.1, one under C4.2. The first is the spec's own "the list is the file" check, and it
  reported "2 the" as written. C4.3's and C4.4's breaks are #14's; this close ran none.
- One tag changed at this close, after the blind rater's pass over the three Defect lines
  (`relabel.py compare`: stage 2 of 3, cause 2 of 3, made 3 of 3). The near-miss defect's cause
  goes from "environment" to "process", as the rater read it: `specs/README.md` names "a break
  run wrong" as process, and CLAUDE.md already names the `core.safecrlf=false` pitfall, so the
  step was known and skipped. Day 2's CRLF diff defect stayed "environment" because no rule
  named its fix beforehand. Its stage stays "spec-change PR" against the rater's "before merge"
  (medium): the rater said the text did not say when, and the line now says "before any code".
- The carriage-return Note held: the list is parsed with `split()`, so a CRLF checkout's "the\r"
  never becomes a word, and the suite passes on Windows and on CI's Linux.
