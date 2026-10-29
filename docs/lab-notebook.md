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

**Day 2 — standard input, a file named `-`.** `python -m wordtally` with no name, or with `-`
among the names, counts standard input as a file named `-`: its own line, one name in the total,
its words in the `--top` tally (H3.1, the Day 3 stop's decision). It is read as UTF-8 bytes, its
carriage returns counted. C1.8's usage error for no name expired (H1.1). Run after Day 3, as the
stop decided.

- *Estimated 3 pull requests, took 3:* the spec change (#11), Track A (#12), and this close. #10,
  before it, recorded the Day 3 stop's decisions in `plan.md`.
- The spec-auditor found three faults in the draft: the tests had to feed bytes but `run()`
  hard-codes `text=True`; C2.3 claimed a text-mode read drops the carriage return on Linux, where
  it does not; C2.4 named `main` as its base, which ticks itself once Track A merges (Day 3's C3.4
  had done the same). Before it ran, the session had found its own C2.4 failing today and a
  CRLF-blind diff counting 109 removed lines. All before any code (#11).
- Track A was written by the implementer on Haiku (37+/9- lines) and taken without a rewrite.
  Its first draft of the stdin test helper left the child's `\r\n` endings; its own run caught
  it. The three new tests were seen red on `main`'s code first, and each was broken once. One
  break, the text-mode read, bites only on Windows: CI's Linux cannot see it.
- Six defects, all found before their PR merged; none escaped from Days 1 or 3. The blind rater
  read "found: self" as before any code for a defect caught in the spec-change PR, the third day
  that tag was miswritten; it was changed, with the one beside it. The spec-auditor's three
  findings had been written as one line and were split, as the rule asks.
- Tokens, 2026-10-28, as `scripts/token-usage.py` counted them at this close: Day 2, 33 replies
  on Opus, 31k output tokens and 1.7M cache reads. The implementer's 7 Haiku replies for #12
  were counted under no day, beside 213 Opus replies off the days' branches. Day 3's Opus rows
  grew from 32 replies to 53: #10 and its own close are now counted.

**Day 4 — `--stopwords`, common words out of the top list.** `--stopwords`, a flag, leaves the
words of `wordtally/stopwords.txt` (45 lowercase English words) out of the `--top` tally and
nothing else: lines, words and characters count them as before, and without `--top` it changes
nothing, as the Day 3 stop decided.

- *Estimated 3 pull requests, took 3:* the spec change (#14), Track A (#15), and this close.
- The spec-auditor found nothing blocking; one of its three notes, that a CRLF checkout's
  "the\r" bites only on Windows, went into the spec. The one defect before code was the
  session's own: a hold break's first run reported git's CRLF warning as its line (#14).
- Track A was written by the implementer on Haiku and taken without a rewrite. Its report said
  the list held 40 words, not 45; review caught it. #15 recorded three breaks but not that the
  new tests were red on the pre-day code; this close ran that, and both failed as the spec said.
- Three defects, one each found in the spec-change PR, review, and the close. The close's is a
  record gap in #15, made and found on Day 4; no code escaped. The blind rater read the CRLF
  break defect as process, not environment, and it was changed: the pitfall was already in
  CLAUDE.md.
- Tokens, 2026-10-28, as `scripts/token-usage.py` counted them at this close: Day 4, 40 replies
  on Opus, 26k output tokens and 2.4M cache reads, and the implementer's 6 Haiku replies, this
  time counted under the day. Day 2's Opus rows grew from 33 replies to 65: its close's own
  session is now counted.

**Day 5 — `--json`, the same counts as one JSON object.** `--json` prints one line, the object
`json.dumps` writes: "files" (name, lines, words, characters per file read), "total" when more
than one file is named, "top" with `--top`, all built from the rows and tally the plain output
prints. Without it the output is Day 4's. Phase 1's Done when holds, and Phase 1 closes.

- *Estimated 3 pull requests, took 3:* the spec change (#17), Track A (#18), and this close.
- The spec-auditor found nothing blocking. Of its three findings, two were taken: the draft said
  no hand-off names Day 5, missing Day 1's Out of scope, and the hold breaks were not yet
  recorded (#17).
- Track A was written by the implementer on Haiku and taken without a rewrite; review wrapped
  two long lines. Its three new tests were each broken once. #18 again did not record that
  they were red on the pre-day code, the gap Day 4's close found in #15. This close ran it,
  and all three failed as the spec said. A Note does not carry a lesson to the next track.
- Two defects: one found by the auditor, one at the close. Neither escaped into code, and none
  escaped from an earlier day.
- Tokens, 2026-10-28, as `scripts/token-usage.py` counted them at this close: Day 5, 17 replies
  on Opus, 11k output tokens and 1.1M cache reads, and the implementer's 6 Haiku replies. Day
  4's Opus rows grew from 40 replies to 54: its close's own session is now counted.

## What is being measured

| Question | Evidence it will be judged on |
| --- | --- |
| Do day-sized estimates hold for agent-implemented work? | Estimated vs actual pull requests per spec (currently Day 1 3→3, Day 3 3→3, Day 2 3→3, Day 4 3→3, Day 5 3→3) |
| Does the word rule survive the days unedited? | Lines changed in `tests/contract/` (currently 0, Days 1, 3, 2, 4 and 5) |
| How much of the implementer's work is redone? | Tracks the main session rewrote beyond review fixes, of the tracks the implementer wrote (currently 0 of 5) |
| Where are defects caught? | Defect lines by `found:` (currently Day 1: 3 auditor, 1 spec-change PR, 1 self, 1 close; Day 3: 1 auditor, 1 spec-change PR, 1 self; Day 2: 3 auditor, 2 spec-change PR, 1 self; Day 4: 1 spec-change PR, 1 review, 1 close; Day 5: 1 auditor, 1 close; 0 escapes from an earlier day) |
| Does a blind reader tag defects the same way? | `relabel.py compare` disagreements per day (Days 1, 3, 2, 4 and 5: in their closing PRs) |

## Retrospective

Written 2026-10-28, after Day 5 closed (#19, `main` at 9a8e331). Five auditors ran in parallel,
each from a fresh context, none reading the others: the plan-auditor on Phase 1 and on the whole
plan, and the security-ops, agentic-engineering and architecture auditors. The maintainer chose to
record their findings and pause, not fix them now.

### Verdicts

| Auditor | Verdict | In one line |
| --- | --- | --- |
| plan-auditor, Phase 1 | holds | Done when run for real: "Ran 23 tests", OK; JSON and plain counts match (1, 7, 27); 13 criteria hold |
| plan-auditor, whole plan | delivered | No code finding; six notes on documents drifting |
| security-ops | unsafe for more autonomy | The agent holds the owner's admin token; protection has `enforce_admins:false` and no required review |
| agentic-engineering | weak evidence | Good process around agents; the task was too small and fixed to test long-horizon capability |
| architecture | promising | Clear rules, but the main gates can be stepped round by accident or on purpose |

They disagreed on whether the frozen word rule is safe. The plan-auditors ran the diff on
`tests/contract/` and found it unedited. The architecture auditor showed two ways that check
misses (open items 4 and 5). They also disagreed on whether the measurements say anything: the
counts check out, but the gap metric is null on every row, and every estimate was 3→3.

### Lessons

- A lesson written only in a day's Notes did not carry: tests were not seen red on the pre-day
  code in #15, and again in #18. Behaviour changed only where a lesson became a rule or a script.
- "Nothing merges without the maintainer" and "wait for merged" are kept by the agent's behaviour,
  not by access control. They held for 20 PRs; nothing would have stopped a break.
- The plan, the contract and the workflow came from the kit's seed commit and the maintainer's
  decisions. The agents settled spec detail and wrote 106 lines of product code. Judge the
  agent evidence at that size.

### Open items, for whoever resumes

None is owned by a day. Before more agent autonomy, 1 to 3 come first.

1. **Agent credentials.** Give agents a non-admin identity (a fine-grained token or GitHub App,
   no `workflow` scope), set `enforce_admins:true`, and require one review from someone who is not
   the author. Today all 20 PRs were authored and merged by the same account, with 0 reviews.
2. **Required checks accept any source.** Five of the six required checks have `app_id:null`:
   any `repo` token can post a passing status by name. Pin each to GitHub Actions.
3. **The control plane is not frozen.** A PR can edit `.github/workflows/` and `scripts/`, and
   `pull_request` runs the PR's own copies. Freeze them or add CODEOWNERS with required review.
4. **A rename empties the frozen set.** Moving `tests/contract/test_word_rule.py` out of
   `tests/contract/` unchanged passes `scripts/invariants.py` (an `R100` rename is allowed); the
   suite drops from 23 tests to 18. Fail renames out of a frozen pattern; fail a drop in test count.
5. **The contract tests do not pin the plan's rule.** Changing the word pattern to `[\w']+` passes
   all five contract cases, which are ASCII only. Add non-ASCII and underscore cases.
6. **Nothing checks the evidence.** No CI step runs a spec's Verify block, re-runs a `broken:`
   line, or checks a ticked criterion's test exists. "Criteria first broken at the close" returns
   nothing even for Day 5, which had such a case.
7. **The local guard has holes.** It sees only shell commands: Edit and Write on
   `~/.claude/settings.json` and the guard itself are not denied, `-XDELETE` and
   `--method=DELETE` pass its DELETE rule, and `gh pr merge` and `git push origin main` are not
   blocked.
8. **Supply chain.** Actions are pinned by tag, not commit SHA, and the Pages job installs
   `numpy` unpinned, with `id-token: write`.
9. **Untrusted text.** The repository is public, so issues and PR text reach the agent, which
   also writes the memory loaded into later sessions. No rule treats that text as data.
10. **Carry the "seen red first" step** into the implementer brief or `scripts/break.py`, not a Note.
11. **Kit leftovers in CLAUDE.md:** "start Day 12", jobmatch's token figures, Maven. They are the
    kit's lessons, not this repository's.
12. **The Done when is shell-dependent.** PowerShell's `cat` adds a CRLF (28 characters, not 27).
    Read it in a POSIX shell.

### Next experiments the audits proposed

- An agent writes the plan and specs for an unseen feature set of about 2k lines. Count the
  maintainer's corrections and the defects that escape.
- Give the implementer the spec alone, not a dictated brief. Count rewrites and escapes.
- Run the spec-auditor from a different model family against specs with planted faults.

## E1: a decision model as an evidence checker

Written 2026-10-29 (`main` at 16e3852), step 6 of the
[workflow improvement plan](workflow-improvement-plan.md#order-of-work). E1 asked whether Jev,
TypeSafe's decision model, can tell if a criterion's `broken:` lines show that its test catches
what the criterion promised: the judgment half of open item 6. The set, labels and bar were
committed before any call (#30); the runner (#31) asked each bundle of Jev, of a fresh Opus agent
per bundle, and of a floor that always answers `supports`; the records and scorer are #32.

**Verdict: no-go.** E1 fails bar 2. As the plan says, the work stops here: no Jev dashboard
section, no shadow days, no adoption (its steps 7 to 11).

| Measure, on 66 scored bundles (3 ambiguous apart) | Jev | Opus agent | Floor | Bar for Jev |
| --- | --- | --- | --- | --- |
| Hand-written `insufficient` and `contradicts` flagged | 17 of 17 | 17 of 17 | 0 of 17 | 1, at least half: met |
| Real `supports` flagged (false alarms) | 12 of 12 | 12 of 12 | 0 of 12 | 2, at most 1 in 10: **not met** |
| Against the Opus agent | same flags, same false alarms | | | 3: met |
| Per bundle | $0.000038, 0.34 s | about 40k tokens, 6–15 s; dollars not recorded | | 4: met on tokens, see below |
| Highest probability stated | 0.89 | 0.90, once | 1.0 | |
| Answer is the label | 31 of 66 | 62 of 66 | 12 of 66 | |
| Brier score | 0.232 | 0.096 | 0.818 | |

Why, from the records:

- **Jev's flags carry no information at the fixed threshold.** Its highest stated probability on
  any bundle is 0.89, so every answer it gave is a flag. Bars 1 and 3 are met by flagging all 66
  bundles, which an answerer that always says "flag" would match.
- **Its labels fail on their own.** It answered `contradicts` 39 times on a set with 5 such
  cases, among them 9 of the 12 hand-written `insufficient` cases and 13 of the 32 swapped pairs.
- **The false alarms are not only Jev's.** The Opus agent also flags all 12 real `supports`, at
  0.55 to 0.85, and answers `insufficient` on 4 of them (R02, R04, R10, R16). With this question,
  no answerer states 0.9 that the breaks cover a criterion. The plan's "the question, not the
  model" note is for both failing bars 1 and 2; here both pass 1 and fail 2, so the record is
  that the question and threshold share bar 2's failure, and Jev's labels (31 of 66, against
  62) fail apart from it. The threshold is not retuned after the answers (ground rules).
- **Bar 4 rests on tokens, not dollars:** the Opus agent's cost was not recorded per bundle
  (#32's departure). It does not change the verdict.
- With 12 real `supports` among 66 bundles, the result is directional, not proof.

What it leaves:

- Open item 6's judgment half stays open. Its mechanical half stands: `scripts/evidence.py` and
  `specs/breaks/` (#24, #25, #26).
- The 4 real cases the Opus agent called `insufficient` were not relabelled. Checking them would
  be a recorded correction under the ground rules, and it cannot change bar 2.
- Trying again would be a new experiment, with a new question or threshold committed before its
  first call. That is the maintainer's decision; nothing here starts it.
