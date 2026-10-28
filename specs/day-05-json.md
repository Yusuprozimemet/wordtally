# Day 05 — `--json`, the same counts as one JSON object

**Phase:** 1 · **Depends on:** Day 4 · **Expected PRs:** 3 (this spec change, Track A, the close)

## Goal
`python -m wordtally --json ...` prints one JSON object holding exactly the counts the same
command prints without `--json`, so that Phase 1's Done when holds: `cat a.txt | python -m
wordtally --json --stopwords --top 3` prints one JSON object whose counts match the plain output's.

## In scope
- `--json`, a flag that takes no value. Without it the output is Day 4's, byte for byte.
- With `--json`, stdout is one line: the object as `json.dumps` writes it with its default
  separators, then a newline. Its keys, in this order:
  - "files": a list, one object per file read, in the order named, each with "name", "lines",
    "words" and "characters". Standard input's name is "-", as on its plain line.
  - "total": an object with "lines", "words" and "characters", present only when the plain output
    prints a total line (more than one file named).
  - "top": a list of objects with "word" and "count", in the plain output's order, present only
    with `--top`. `--stopwords` filters it as it filters the plain list.
- A file that cannot be read is reported on stderr as before and left out of "files"; the exit
  status is 1, as before, and stdout still holds one JSON object.

## Out of scope
- Any other format (CSV, a JSON line per file) or pretty-printing: `plan.md` names one object.
- Any change to the word rule: `tests/contract/` is frozen.

## Tracks

| Track | Owner | Work |
|---|---|---|
| A | implementer | `wordtally/__main__.py`: `--json`, the object built from the rows and the tally the plain output prints; `tests/test_cli.py`: the three tests C5.1–C5.3 name, added, no other test edited |

No Track 0: the two **hold** checks, C5.4 and C5.5, exist today, and their breaks are in this
spec-change PR.

## Acceptance criteria
The tests write their files as bytes in a temporary directory and pass full paths, as Day 1's
do. Standard input goes in as bytes through `run_with_input`.

- [x] C5.1 **new** — Phase 1's Done when, exactly: with "The cat and the dog, a cat" and a newline
      on standard input, `python -m wordtally --json --stopwords --top 3` prints exactly
      `{"files": [{"name": "-", "lines": 1, "words": 7, "characters": 27}], "top": [{"word":
      "cat", "count": 2}, {"word": "dog", "count": 1}]}` (one line) and a newline, and exits 0.
      Test: `CliTest.test_json_prints_the_counts_as_one_object`. Red today: exit 2, nothing on
      stdout, "unrecognized arguments: --json" on stderr.
      Evidence: `CliTest.test_json_prints_the_counts_as_one_object` (#18), seen red on
      `ea0af5d`'s code at this close: "Tuples differ: (2, '') != (0, ...)". The Verify command
      prints the object on `main` (`4304d91`), exit 0.
      broken: json.dumps given compact separators in wordtally/__main__.py → AssertionError: Tuples differ: (0, '{"files":[{"name":"-","lines":1,"words":7,"charact[67 chars]}\n') != (0, '{"files": [{"name": "-", "lines": 1, "words": 7, "[84 chars]}\n') (#18)
- [x] C5.2 **new** — the JSON matches the plain output: for a.txt "the cat" and b.txt "the dog
      sat", each with a newline, `--json --top 2 a.txt b.txt` and `--top 2 a.txt b.txt` both exit
      0, and the JSON's "files", "total" and "top", read back with `json.loads`, equal the plain
      output's rows, total line and top lines, parsed field by field. Test:
      `CliTest.test_json_matches_the_plain_output`. Red today: as C5.1.
      Evidence: `CliTest.test_json_matches_the_plain_output` (#18), seen red on `ea0af5d`'s code
      at this close: "Tuples differ: (2, 0) != (0, 0)", the two exit statuses.
      broken: the JSON top list reversed in wordtally/__main__.py → AssertionError: Lists differ: [{'word': 'cat', 'count': 1}, {'word': 'the', 'count': 2}] != [{'word': 'the', 'count': 2}, {'word': 'cat', 'count': 1}] (#18)
- [x] C5.3 **new** — a file that cannot be read: `--json missing.txt a.txt`, missing.txt not
      existing, exits 1, names missing.txt on stderr, and prints one JSON object whose "files"
      holds a.txt alone and whose "total" equals a.txt's counts. Test:
      `CliTest.test_json_leaves_out_a_file_that_cannot_be_read`. Red today: exit 2, as C5.1.
      Evidence: `CliTest.test_json_leaves_out_a_file_that_cannot_be_read` (#18), seen red on
      `ea0af5d`'s code at this close: "2 != 1".
      broken: the JSON branch exits 0 after a failed file in wordtally/__main__.py → AssertionError: 0 != 1 (#18)
- [x] C5.4 **hold** — Days 1–4's behaviour stands: the 20 tests today pass, and none is edited:
      `git diff ea0af5d -- tests/test_cli.py | grep -c '^-[^-]'` prints 0 (grep exits 1 when it
      does). `ea0af5d` is `main` before this day.
      broken: a line of test_top_below_one_is_a_usage_error edited in tests/test_cli.py → removed=1
      broken: a line only added to tests/test_cli.py, the near miss → removed=0
      (Both ran with the count printed, and the near miss with the check inverted, so that
      "failed" means the grep counted 0.)
      Evidence: after #18, the suite runs 23 tests, OK, and the diff command prints 0 on `main`
      (`4304d91`); broken in #17.
- [x] C5.5 **hold** — the word rule is untouched: `python -m unittest tests.contract.test_word_rule`
      passes and `git diff --exit-code --stat ea0af5d -- tests/contract/` prints nothing.
      broken: a space added to a line of tests/contract/test_word_rule.py → 1 file changed, 1 insertion(+), 1 deletion(-)
      broken: words() split on whitespace in wordtally/count.py → AssertionError: Lists differ: ['Hello,', 'world!'] != ['Hello', 'world']
      Evidence: on `main` (`4304d91`), `tests.contract.test_word_rule` gives OK and the diff
      prints nothing, exit 0; broken in #17.

## Verify
```bash
python -m unittest discover -s tests -t .    # Ran 23 tests, OK (5 contract, 18 CLI)
git diff ea0af5d -- tests/test_cli.py | grep -c '^-[^-]'    # 0
git diff --exit-code --stat ea0af5d -- tests/contract/      # nothing, exit 0
printf 'The cat and the dog, a cat\n' | python -m wordtally --json --stopwords --top 3
```

The last command prints C5.1's object.

## Notes
- No `Hand-off` line names Day 5, but Day 1's Out of scope does: "`--json` — Day 5, whose keys
  follow this day's three names". In scope's "lines", "words" and "characters" take it up. Days
  2–4's Out of scope name `--json` for Day 5 without a condition. Day 4's and the Day 3 stop's
  decisions (`plan.md`, Course corrections) are the premises: standard input is the file "-",
  `--stopwords` filters only the top list.
- The spec-auditor ran before this PR: ready, nothing blocking, 3 findings. Two are taken: the
  first draft's Note said no hand-off names Day 5, missing Day 1's line above; and the hold breaks
  were promised but not yet recorded. The third needs no change: `'^-[^-]'` misses a removed blank
  line, accepted on Day 4.
- **Defect** — found: auditor · cause: spec · made: Day 05 · the first draft's Notes said no
  hand-off names Day 5; Day 1's Out of scope names its key names. Fixed in this PR (#17),
  before any code.
- `scripts/break.py` judges a check by its exit code, and C5.4 passes when grep exits 1, so its
  breaks ran through a wrapper that prints "removed=N" and fails on the wrong count, as Day 4's did.
- `scripts/spec-drift.py` still prints "Day 03 is done: stop and evaluate before going on" (Day 4's
  Notes say why); Days 2 and 4 ran under the same message.
- Day 5 closes Phase 1 and the project (`specs/README.md`, Stopping points). The close runs the
  plan-auditor on Phase 1 and the whole plan, and the three end-of-phase auditors (CLAUDE.md).
- A Windows path in JSON has its backslashes escaped, so C5.2 and C5.3 compare parsed objects,
  not strings with a path in them. C5.1 reads standard input, whose name "-" needs no escape.
- **Defect** — found: close · cause: process · made: Day 05 · #18 recorded three breaks but not
  that C5.1–C5.3's tests were seen red on the code before the day: the gap Day 4's close found in
  #15, repeated. Day 4's Note recorded it, but no rule or brief carries it to the next track. Run
  at this close: with #18's `tests/test_cli.py` over `ea0af5d`'s code, all three fail, "Ran 3
  tests", "FAILED (failures=3)", exit 2 as "Red today" says.
- **Rewrite** — Track A: none. The implementer's code (#18) was taken after review, which
  wrapped two lines over 110 characters.
- Track A's three breaks are recorded under the criterion whose test they turned red, one each.
  C5.4's and C5.5's breaks are #17's; this close ran none.
- The end-of-phase audits run once this close merges (CLAUDE.md, A day, step 6): the
  plan-auditor on Phase 1 and the whole plan, and the security-ops, agentic-engineering and
  architecture auditors, each from a fresh context.
- The blind rater's pass over the two Defect lines (`relabel.py compare`: stage 1 of 2, cause 2
  of 2, made 2 of 2) changed no tag. It read the auditor's defect as found before merge (low),
  as the text did not say which PR fixed it. The tag stays: the spec-auditor ran before #17, so
  before any code, and the line now names #17.
