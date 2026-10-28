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

**Day 3 — `--top N`, the most frequent words.** `python -m wordtally --top N FILE...` prints,
after the count lines and the total, the N most frequent words of every file read, case folded,
as "COUNT WORD", count descending and then the word ascending. Without `--top` the output is Day
1's. Phase 0's "done when" holds.

- *Estimated 3 pull requests, took 3:* the spec change (#7), Track A (#8), and this close. #6,
  before it, was dashboard work outside the day.
- The spec-auditor found the draft's C3.4 had no command whose output passes or fails; it became
  a `grep -c` broken both ways (#7). That PR's first run of those breaks never started (WSL's
  `bash`), and `break.py` printed `broken:` lines anyway; caught and re-run before #7 opened.
- Track A was written by the implementer on Haiku (45+/10- lines) and taken without a rewrite.
  Its first draft printed "a 2" for "2 a"; its own test run caught it. The three new tests were
  seen red on `main`'s code first, and each was broken once.
- Three defects, all found before their PR merged; none escaped from Day 1. The blind rater
  disagreed with two tags, and both were the errors Day 1's close had already corrected:
  "found: self" for a defect caught in the spec-change PR, and "made: none" for the day's own
  work. Both were changed. The rule was written down, but the tagger did not keep to it.
- Tokens, 2026-10-28, as `scripts/token-usage.py` counted them at this close: Day 3, 40 replies
  (32 on Opus, 8 on Haiku), 34k output tokens and 2.0M cache reads, against Day 1's 111 replies
  and 8.2M. Day 1's rows grew at this recount (80 replies then): its close's own session is now
  counted.

## What is being measured

| Question | Evidence it will be judged on |
| --- | --- |
| Do day-sized estimates hold for agent-implemented work? | Estimated vs actual pull requests per spec (currently Day 1 3→3, Day 3 3→3) |
| Does the word rule survive the days unedited? | Lines changed in `tests/contract/` (currently 0, Days 1 and 3) |
| How much of the implementer's work is redone? | Tracks the main session rewrote beyond review fixes, of the tracks the implementer wrote (currently 0 of 2) |
| Where are defects caught? | Defect lines by `found:` (currently Day 1: 3 auditor, 1 spec-change PR, 1 self, 1 close; Day 3: 1 auditor, 1 spec-change PR, 1 self; 0 escapes from an earlier day) |
| Does a blind reader tag defects the same way? | `relabel.py compare` disagreements per day (Days 1 and 3: in their closing PRs) |

## Retrospective
