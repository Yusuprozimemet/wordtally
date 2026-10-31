# Specs

Spec-driven development. **No code without a spec. No spec without checkable acceptance criteria.**

## Workflow

1. Read the day spec against the code, and run every acceptance check on the code as it is.
   Fix what that turns up in a spec-change PR before any track starts.
2. Branch per track: `day-04/track-b-saved-jobs-tests`.
3. Build only what **In scope** lists.
4. Copy the acceptance criteria into the PR description and tick them.
5. The day is done when every box is ticked and **Verify** passes on `main`.

## Short specs

For one small behaviour change outside the days that fits one PR and touches no contract test
or frozen file, use a short spec. Do not use one for work covered by a day's criteria or for a
change needing a `Replaces:` line. Use the day workflow for those.

On `change/<slug>` (lowercase letters, numbers and single hyphens), write
`specs/changes/<slug>.md` using [`_short-template.md`](_short-template.md). Its criteria use
`S-<slug>.N` IDs, `new` or `hold` tags and `Test:` fields, as in a day spec. Spec and code
land together: no separate spec-change or closing PR. Put the `seen red:` line and the
`broken:` lines in the PR. Run `python scripts/track-red.py --branch change/<slug>` to check each new criterion's
test against base code and the head; CI runs the same check. Hold checks must also
be broken on purpose as in the day rules below.
Tick each criterion in the same PR once its seen-red or broken evidence is in the PR body.
Ticked short-spec criteria join the behaviour index; a later day replaces one with
`Replaces: S-<slug>.N`.

## Rules

- **The spec is the contract.** Found work outside it? Add a line to that day's *Notes*
  and raise it. Do not widen the PR — CI rejects diffs over 400 lines.
- **Criteria must be checkable by someone who did not write the code.**
  "Auth works" is not a criterion. "`POST /api/auth/login` returns 200 with a
  `Set-Cookie` containing `HttpOnly` and `SameSite=Lax`" is.
- **Every criterion is `new` or `hold`, and every check has been seen to fail.** A check that
  cannot fail proves nothing, and in jobmatch-microservices, Phases 0 and 1 had three kinds of
  them: a CI gate that never ran the integration tests (Day 02), a verify command that ran no
  tests (Day 08), and greps for TODO markers that did not exist, so the criterion ticked itself
  (Days 08 and 09).
  - `new` is behaviour that does not exist yet. The check must fail on today's code, and the
    spec says how ("the grep finds two"). A `new` check that passes before the work is wrong.
    `scripts/seen-red.py` runs a track's tests on the code before it and prints the `seen red:` line.
  - `hold` must stay true through the change: contract tests passing unedited, a statement
    count. It passes before and after, so passing says nothing. Break the code on purpose once,
    watch the check fail, record what it reported, and revert. In jobmatch-microservices, Day
    08 did this with a per-posting loop: the query-count test failed with 2, 21 and 25
    statements.
  - The proof goes in the PR that first runs the check: the spec-change PR if the check exists
    already, the track's PR if a track adds it (a Track 0). The closing PR links it when it
    ticks the box.
  - The record is one line of its own: `broken: <what was broken> → <what the check reported>`,
    or `broken: none → <why>` in a PR that broke nothing. The PR that ran the break carries it
    in its description; the closing PR copies it under the criterion it ticks. `spec-drift.py`
    reads no other wording as a break. `scripts/break.py` runs one break and
    prints the line.
  - A grep is broken both ways: once with the thing it looks for put back (it must find it),
    once with a near miss it must not match (a longer name, a fully qualified form, a comment).
    In jobmatch-microservices, two of the paper's escapes were greps that matched too much or
    too little (D22-017, D23-028).
  - The closing PR copies breaks; it does not run the first one. A criterion whose only
    `broken:` lines the close itself ran was a check no track had shown can fail: record it as a
    `Defect` (`found: close`). In jobmatch-microservices, four of the paper's six spec escapes
    were these. After the merge,
    the dashboard lists them under "Criteria first broken at the close".
- **A contract test's timing is part of what it expects.** A test in `tests/contract/` is frozen in its expected values and in when it expects them. One that asserted
  an effect at once and now waits for it, or waits longer than it did, expects something else,
  even with every value unedited. In jobmatch-microservices, Day 25 did this to
  `AccountDeletionIT`: the saved jobs came to go by the `user.deleted` event,
  the test came to poll apps_db for 10 s, and deletion became eventually consistent through the
  public API, a `savedCount` that counts a deleted user's saves for a few seconds. The edit was
  approved, but read as values only, and no test asserted that count until #441 (paper, §4.1).
  So a new or longer wait, poll bound or timeout in a contract test is a departure: the
  spec-change PR names it before the work, with the bound and what the API shows until it
  passes; the maintainer approves it; and a test outside `tests/contract/`
  pins that public effect within the bound, as, in jobmatch-microservices,
  `SavedCountAfterDeletionIT` does. A wait raised to quiet a flaky test is
  the same change.
- **Tracks inside a day run in parallel. Days run in order.** Day N assumes N-1 is merged.
- **Record every defect in the day's *Notes* when it is found**, one `Defect` line each, with
  three fields:
  - `found:` where, exactly one of `auditor`, `spec-change PR` (before any code); `review`,
    `break on purpose`, `self`, `Track <X>` (before merge); `close`, `dashboard`,
    `Day <NN> review` (after the track merged: an escape).
  - `cause:` exactly one of `spec` (wrong, missing a case, or not meetable as written),
    `implementation` (the spec was right, the code did not do it), `process` (the workflow and
    the record around the code: branch names, Jira keys, a break run wrong, a track announced
    and never opened) or `environment` (tooling, CI, the machine, a library).
  - `made:` the day whose merged work holds the defect (`Day 21`, or `none` for work outside any
    day). When it is not this day, the defect is an escape from that day, whatever `found:` says.

  One line per problem: the same kind of problem in two PRs is two lines, and a review of seven
  drafts is as many lines as it finds problems. In jobmatch-microservices, the paper had to
  decide all three of these after the data (its §5.3); deciding them on the day is cheaper. A
  track whose code the main session rewrote beyond review fixes gets a `Rewrite` line. In
  jobmatch-microservices, these are the counts `docs/paper/success-criteria.md` judges H1–H3 by; its
  amendment maps `process` and the `found:` values above.

  At the close, a reader who wrote none of it labels them again, blind
  ([`scripts/relabel.py`](../scripts/relabel.py), the `defect-rater` agent): the tagger has also
  written the work, and in jobmatch-microservices, on Days 21–28 a blind rater disagreed with 11 of 82 causes and 16 stages,
  mostly defects made on one day and found on another. The closing PR lists each disagreement
  and decides it: the tag kept, with the reason, or changed in the Notes. A tag is never changed
  without a line in the PR.
- **IDs.** Each criterion starts with its ID, `C28.3` for Day
  28's third, and keeps it when others are added or dropped. Each item a day leaves for later is
  a `Hand-off` line in its Notes with an ID, `H28.1`, and the day or the maintainer it goes to.
  The receiving spec picks it up by citing the ID; naming the day does not. `spec-drift.py`
  lists what no later day picks up, and any track a PR announces ("E1c, next") that no branch
  ever names.
- **When a criterion changes behaviour in force, name what it replaces.** Put
  `Replaces: C12.3 — was: <the old behaviour, quoted or in one sentence>` inside the new
  criterion's block, in the spec-change PR like any criterion wording. A reviewer then sees the
  old and the new behaviour, and `python scripts/behaviour-index.py` retires the old criterion
  once the new one is ticked; a `Replaces:` line without an ID or `— was:` fails it. Never edit
  the replaced criterion's file.
- Changing a spec is normal. Change it in a PR *before* the work, not after.
- Specs written before the `new`/`hold` rule get their criteria tagged in that day's
  spec-change PR, when the spec is read against the code.

## Layout

```
specs/
  README.md        this file
  _template.md     start a new day from this
  day-NN-slug.md   one file per day
```

## Map to plan.md

| Days | Phase | Outcome | Status |
|---|---|---|---|
| 1, 3 | 0, Counting | lines, words and characters per file; the most frequent words | done (#9) |
| 2, 4-5 | 1, Input and output | standard input; stopwords; JSON output | done (#19) |

## Provisional specs

None yet. Each day's spec is written on its day, from `plan.md` and the code as it is.

## Stopping points

- **Day 3** ends Phase 0: the tool counts lines, words and characters and lists the most
  frequent words, on files named on the command line. `plan.md` marks it **Stop and evaluate.**
- **Day 5** ends Phase 1, and the project: standard input, stopwords and JSON output.
