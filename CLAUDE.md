# Working in this repository

This repository builds `wordtally`, a command-line word counter in Python, one day spec at a
time, and records what each day turned up. Three layers have to agree: [`plan.md`](plan.md) is the goal and
changes rarely; the day specs in [`specs/`](specs/) are the steps; the code is where the steps
land. The spec rules are in [`specs/README.md`](specs/README.md) and the template in
[`specs/_template.md`](specs/_template.md). This file is the working order and the lessons the
rules do not state. [`docs/workflow.md`](docs/workflow.md) draws it.

**Source of truth, when they disagree:** the code on `main` for what the system does; the merged
spec for what a day promised; `plan.md` for the goal. The dashboard and memory only record
the others: correct them, never the other way round.

## Starting

A person or an agent new to this repository: read `plan.md`, then run
`python scripts/behaviour-index.py` to see what the system does now, then `specs/README.md`; run
`python scripts/spec-drift.py --out spec-drift.json` (it needs `numpy` and the `gh` CLI; or open
the dashboard) for the current day and next step; then ask for it, for example "start Day 12". Nothing merges without the
maintainer, and nothing starts after a phase ends until they say so.

## A day, in order

1. **Audit before writing anything.** On the first day of a phase, run the **plan-auditor**
   agent on the phase first: do the specs still add up to what `plan.md` wants from it, and
   does the code still match their premises? Then, every day, run the **spec-auditor** agent on
   the day: every check run on the code as it is, every `hold` tried to break, every claim
   counted. Both only report. Fix what they find in a **spec-change PR** first (a **plan-change
   PR** when the code shows `plan.md` itself is wrong, which should be rare):
   `day-NN/spec-<slug>`, titled `Day NN spec change: <what was wrong>`. Every criterion is tagged
   `new` (fails today; the spec says how) or `hold` (true today; broken on purpose once).
2. **One PR per track**, each branched from fresh `main` after the previous one merged. Never
   stack branches. `day-NN/track-<letter>-<slug>`, titled `Day NN track X: <what it does>`. A
   Track 0 holds the tests that must pass before and after the change, and lands first.
3. **A closing PR:** `day-NN/close-the-day`. Tick each criterion with its evidence (test or
   command, and the PR it landed in), add Notes to the spec, and update the Day entry and measurement
   table in [`docs/lab-notebook.md`](docs/lab-notebook.md) (the README keeps only its Findings). Run `python scripts/token-usage.py` and commit the refreshed
   `docs/dashboard/token-usage.json`: CI cannot read the transcripts it counts. Then relabel the
   day's defects blind: `python scripts/relabel.py blind specs/day-NN-*.md --out <dir>`, give
   `<dir>/blind.md` to the **defect-rater** agent, save its JSON as `<dir>/labels.json`, run
   `python scripts/relabel.py compare <dir>`, and put its lines in the PR with a decision on each
   disagreement: the tag kept, and why, or changed in the Notes.
4. **After opening any PR, stop and wait for the maintainer to say "merged".** Do not start the
   next step, and do not start a new phase, until told.
5. **After every "merged", refresh the dashboard before the next step:** the merge rebuilds the
   [public one](https://yusuprozimemet.github.io/wordtally/) by itself (`.github/workflows/dashboard.yml`). On fresh
   `main`, run `python scripts/spec-drift.py` and report the next step it prints. The page on
   GitHub Pages is the only dashboard; nothing else is republished.
6. **When a phase's last closing PR has merged,** after step 5, on fresh `main`: run the
   plan-auditor on the phase that just ended and on the next (at Day 5, the close of Phase 1,
   the three end-of-phase auditors too), report, and stop. They never run inside the closing PR.

Tracks may run in a different order from the spec's table when one depends on another; say so in
the PR.

## One session per step

Every reply re-reads the whole conversation, and that re-reading is most of what the project
costs: in jobmatch-microservices, up to Day 17, 64% of the main sessions' context tokens were read after a session had
passed 300k (the Tokens panel on the dashboard, "context per reply"). So a step starts in a fresh
session: after reporting the next step in step 5, suggest the maintainer start a new session for
it (or `/compact` if they keep this one). Nothing is lost: the spec, `spec-drift.json`, this file
and memory carry what the next step needs.

Output that lands in the main session is re-read by every later reply. Keep it small:

- Test output and CI logs: filter to the failures and the counts (`grep`, `tail`), or have a
  subagent read them and return the summary. Never print a whole log or report.
- Read the part of a file you need (`offset`/`limit`, `grep -n`), not the whole file, unless the
  step changes all of it. Diffs: `--stat` first, then the files that matter.

## The auditors

`.claude/agents/plan-auditor.md` and `.claude/agents/spec-auditor.md`. Separate agents with their
own brief and a fresh context, so the session that implements is not the only one checking its
own specs: in this repository that session has read past its own errors more than once.

| When | Run | What it answers |
|---|---|---|
| first day of a phase, before anything else | plan-auditor | Do this phase's specs still deliver what `plan.md` wants, on today's code? |
| every day, before the spec-change PR | spec-auditor | Is every claim and check in this day's spec true, and can each check fail? |
| a phase's last closing PR has merged, on fresh `main` | plan-auditor | What did the phase change that the next one must know? |
| a stopping point `plan.md` names, before going on | plan-auditor, on the whole plan | Is `plan.md` still the right plan, and what has piled up that no day owns? |
| Day 5's closing PR has merged (the close of Phase 1), on fresh `main` | security-ops-auditor, agentic-engineering-auditor, architecture-auditor | Can the workflow take more autonomy safely; what does it show about agents; do its gates hold? |
| every close, after the Notes are written | defect-rater, on `relabel.py`'s blind file | Does a reader who did not write the day tag its defects the same way? |
| any time, by hand | either | "use the plan-auditor on Phase 3" |

Both check hand-offs: what earlier days' Notes and test comments defer to a later day. Nothing
else carries them forward, and that is where most gaps have come from.

The three end-of-phase auditors run once, on Opus, after Day 5's closing PR has merged (the close of Phase 1), on fresh `main`, beside the plan-auditor on the last phase and on the whole plan. Each runs from a fresh context and reads none of
the others' reports: their disagreement is part of the result.

Their findings are advice to the maintainer. What becomes a PR is the maintainer's call.

"Read-only" is enforced, not only stated: `.claude/settings.json` runs `scripts/auditor-guard.py`
on every Bash command and every subagent's stop, and for the five auditors with Bash it blocks a
git or `gh` command that writes and, at the auditor's stop, sends it back if the repository
changed; the main session and other agents pass. The hooks sit in the project settings, not in
the agents' frontmatter: the VS Code extension's Claude Code (2.1.312) ignores frontmatter hooks.
An edit to `.claude/` takes effect in the next session, not this one.

## The implementer

`.claude/agents/implementer.md`, on Haiku (`claude-haiku-5-5`, its `model:` line): the maintainer's
choice, so that code is written by a smaller model and everything else stays with the main session. For each track, the main session
writes the brief (files, changes, tests), sends it, and then does what the implementer does not:
reviews the diff, runs the full checks in "Before pushing", breaks the code on purpose, commits,
and writes the PR. Specs, audits, spec-change PRs and closing PRs stay with the main session. The
implementer never commits or pushes.

## Before pushing

- The tests: `python -m unittest discover -s tests -t .`, from the repository root. Nothing is built first, and CI
  ("Unit tests", `.github/workflows/tests.yml`) runs the same command and nothing more.
- unittest writes no report: read its `Ran N tests` and `OK` or `FAILED (...)` lines, not the
  exit code, and check N is the count the change should give.
- A test that passes before and after a change proves nothing until it has been seen to fail.
  Break the code on purpose, run it, record what it reported, revert. The break never merges.
  Record it in one line, `broken: <what> → <what it reported>` (`specs/README.md`): the
  dashboard reads no other wording. `scripts/break.py` does one break this way and prints the
  line: one exact replacement, the file's bytes put back, the command run without a shell, Maven
  only with `clean`. Hand-run breaks here have half-applied, skipped the compile, never started
  Maven, and lost unstaged work.
- A `new` criterion's tests must also fail on the code before the day. In a track that adds them,
  run `python scripts/seen-red.py -- python -m unittest discover -s tests -t .`: it runs the
  branch's tests on `main`'s code in a scratch worktree and prints `seen red: ... → <what it
  reported>` for the PR. Exit 1 means they pass there. A Note was not enough: #15 and #18 skipped it.
- The PR diff must stay under **400 changed lines** (CI: "Diff stays reviewable"). If it does not,
  split the PR along a line where each part stands alone. An `Oversized:` line in the
  description turns the failure into a warning. Used: none yet. `main` is protected, so the check must
  pass before a merge.
- A grep criterion cannot tell a comment from code: do not name, in a comment, the thing the
  day's grep checks is gone.

## Stop and ask, do not patch

- A change that needs an edit to `tests/contract/`: the word rule, what counts as a word. Those
  tests are frozen (`spec-drift.config.json`, CI's "Frozen files stay unedited"); new tests
  may be added beside them, in `tests/`. Moving one out of `tests/contract/`, or any change that
  lowers the count of `def test_` lines under `tests/`, fails the same check.
  That is the signal the spec's premise is wrong.
- A criterion cannot be met as written. Record the departure; do not deviate silently.

## Where things live

- **Code:** `wordtally/`, the package (`python -m wordtally FILE...` runs it); `tests/`, unittest,
  with `tests/contract/` frozen.
- **Measurement:** `python scripts/spec-drift.py --out spec-drift.json` rebuilds the project
  dashboard's data from git and GitHub; `--build` writes the page (`docs/dashboard/`) with it.
  Every merge to `main` republishes it to [GitHub Pages](https://yusuprozimemet.github.io/wordtally/).

## Pitfalls this repository has already hit

- A small out-of-day behaviour change still needs a seen-red test: use [Short specs](specs/README.md#short-specs) when it qualifies.

On Windows, in Git Bash and PowerShell:

- The working tree is CRLF (`core.autocrlf`). Exact-string edits from Python fail on it: use the
  Edit tool, or normalise CRLF and write the ending back. A test that writes a file writes bytes
  (`"wb"`): text mode adds a carriage return and changes every character count (Day 1, PR #1).
- Long heredocs break in Git Bash, and PowerShell has none. Write commit messages and PR bodies
  to a scratch file (`git commit -F`, `gh pr create --body-file`); give the maintainer one-line
  commands, with any JSON in a file (`gh api --input <file>`).
- The Write tool will not overwrite a file this session has not read, even one a shell made.

Breaks on purpose:

- Run them with `PYTHONDONTWRITEBYTECODE=1` and every `__pycache__` deleted; name the exact test
  (`tests.test_cli.CliTest.<name>`); check that the run FAILED, since `errors=1` proves nothing.
- Run the break, then copy its `broken:` line from what `scripts/break.py` printed. Day 1's first
  draft wrote one before running it, and the report differed.
- On a `git diff --exit-code` check, run `git -c core.safecrlf=false diff ...`, or `break.py`
  reports git's CRLF warning as the check's line.

The dashboard script and the PR checks:

- `scripts/spec-drift.py` reads `main` by name: on a branch it shows `main`. To see a branch's
  effect, clone into a scratch directory, merge the branch with `--no-ff`, and run there. Pass
  `--cache <scratch>/c.json` by hand; `--build` and `--out` do not go together. Its output holds
  an en dash: grep it with `grep -a`.
- In a spec, put in backticks only identifiers, paths and commands; quote literal output. The gap
  reads backticked snake_case and camelCase names as code.
- CI runs `scripts/behaviour-index.py` to check `Replaces:` lines.
- Before pushing: `PR_BRANCH=<branch> PR_TITLE="<title>" python scripts/pr-names.py main HEAD`,
  `git diff --numstat main...HEAD`, and `python scripts/check-links.py` on each Markdown file
  touched. Re-read the PR body's counts and `broken:` lines. Never force-push without the
  maintainer's OK.

## Commits and pull requests

- Commit messages: a subject that says what changed, then why, and what was seen failing.
- PR descriptions follow `.github/pull_request_template.md`: what was built, why this approach
  (including what was broken on purpose and what it reported), contract impact, how to run, and
  the self-check. Spec-change PRs tick the `new`/`hold` line.
- Record mistakes, including your own, in the PR and the day's Notes. The corrections are part of
  what this repository measures.
