# wordtally plan

<!-- plan.md says what and why; the day specs in specs/ say how. It changes rarely, and only in a
plan-change PR. Keep it short. -->

## Verdict: the counting is easy; agreeing on what a word is, and keeping it, is the hard part

`wordtally` starts as one function and a command line that prints the number of words in each
file named. It ends as a small counter: lines, words and characters per file, the most frequent
words, standard input, a stopword list and JSON output. What makes it hard is that every feature
leans on one rule, what counts as a word, and that rule must not drift while the features land.

| Hard part | Why | Fix |
|---|---|---|
| **The word rule** | `count.py`'s `WORD` decides every count; a feature that "fixes" it changes every earlier result | Frozen in `tests/contract/` from the start; a change is a plan-change PR |
| **The output format** | Each day adds to what a line prints; scripts that read it break | Phase 0 settles the per-file line; Phase 1 adds `--json` beside it, not instead |

## Decisions made before the work

- **Python 3.10+, standard library only:** it runs wherever Python does, and CI needs no installs.
- **unittest, not pytest:** no dependency, and `python -m unittest` is the one test command.
- **A word is a run of letters, digits and apostrophes** (`[A-Za-z0-9']+`): "don't" is one word,
  "e-mail" is two. Pinned by `tests/contract/`.

## Target structure

```
wordtally/
  __init__.py
  __main__.py     the command line: python -m wordtally [options] [FILE...]
  count.py        the word rule and the counts
  stopwords.txt   the built-in stopword list (Day 4)
tests/
  contract/       the word rule, frozen
  test_*.py
```

## Phases

Each phase is a series of <400-line PRs, so CI stays green.

### Phase 0 — Counting
**Goal:** the counts a person asks of a text file, on files named on the command line.
- Day 1: lines, words and characters per file, as `wc` prints them, and a total line for more than
  one file.
- Day 3: `--top N`, the N most frequent words, case folded.
- **Done when:** `python -m wordtally --top 3 a.txt b.txt` prints each file's counts, the total and
  the three most frequent words, and `python -m unittest discover -s tests -t .` passes.

### Phase 1 — Input and output
**Goal:** wordtally reads what a pipe gives it and writes what a script can read.
- Day 2: standard input when no file is named, or the name is `-`.
- Day 4: `--stopwords`, with a built-in English list in `wordtally/stopwords.txt`.
- Day 5: `--json`, the same counts as one JSON object.
- **Done when:** `cat a.txt | python -m wordtally --json --stopwords --top 3` prints one JSON
  object whose counts match the plain output's.

## Stopping points

- **Day 3 (Phase 0's counting) is a stopping point.** The plan-auditor reads the whole plan
  against the code before anything goes on. It decides one thing Phase 1 needs: whether standard
  input counts as a file named `-` in the total, or stands alone.

## Constraints

- The word-rule tests in `tests/contract/` are never edited.
- Standard library only: no `requirements.txt`.

## What we are not doing

- **No packaging for PyPI.** `python -m wordtally` is the interface.
- **No languages but English in the stopword list.** One list shows the mechanism.

## Course corrections

<!-- Added by plan-change PRs, newest first: what a stopping point or audit found, and what the
maintainer chose. Empty at the start. -->

## Day-by-day specs

The phases are broken into day specs in [`specs/`](specs/). Read
[`specs/README.md`](specs/README.md) for the workflow.

Day 2 was numbered when the plan was first drafted, but it runs after the stop: how standard input
is counted is the stop's decision.

1. Phase 0: Days 1, 3. **Stop and evaluate.**
2. Phase 1: Days 2, 4-5.
