# Lab notebook

## Results to date

Recorded as they happen, including the ones that make the method look worse.

**Day 1 — lines, words and characters per file.** `python -m wordtally FILE...` prints each
file's lines, words (the frozen word rule) and decoded characters in `wc`'s column layout, a
total line when two or more files are named, and one stderr line per file it cannot read.

- *Estimated 3 pull requests, took 3:* the spec change (#1), Track A (#4), and this close. #2
  and #3, between them, were dashboard and CLAUDE.md work outside the day.
- The plan-auditor found `plan.md`'s "as `wc` prints them" open to six readings on the seed's
  code; the spec-auditor found two more in the draft, one a character count `wc -m` does not
  print; and the session caught a break it had recorded before running it. All four were found
  before any code (#1).
- Track A was written by the implementer on Haiku (about 27.5k tokens, 11 tool uses, 39 s,
  86+/12- lines) from a brief carrying the spec's exact outputs, and taken without a rewrite. Its
  seven new tests were seen red on `main`'s code first, and one break turned C1.5's test red.
- Six defects in all, every one found before its PR merged except one: two `broken:` lines in #1
  hold an arrow the dashboard splits on, found at this close.
- Tokens, 2026-10-28, as `scripts/token-usage.py` counted them at this close: Day 1, 80 replies
  (73 on Opus, 7 on Haiku), 59k output tokens and 5.4M cache reads; another 80 replies off the
  day's branches (setup and #2, #3), 54k output tokens.

## What is being measured

| Question | Evidence it will be judged on |
| --- | --- |
| Do day-sized estimates hold for agent-implemented work? | Estimated vs actual pull requests per spec (currently 3→3) |
| Does the word rule survive the days unedited? | Lines changed in `tests/contract/` (currently 0, Day 1) |
| How much of the implementer's work is redone? | Tracks the main session rewrote beyond review fixes, of the tracks the implementer wrote (currently 0 of 1) |
| Where are defects caught? | Defect lines by `found:` (currently Day 1: 3 auditor, 1 spec-change PR, 1 self, 1 close; 0 escapes from an earlier day) |
| Does a blind reader tag defects the same way? | `relabel.py compare` disagreements per day (Day 1: in its closing PR) |

## Retrospective
