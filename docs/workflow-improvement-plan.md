# Workflow improvement plan: a decision model as a checker

<!-- What to try next on the workflow, and the bar it must clear before it joins it. Nothing here
changes CLAUDE.md, plan.md or a gate. Adoption is a later PR, and only if an experiment passes. -->

## Verdict: close item 6's mechanical half, test a model offline on Days 1–5, then in shadow on new days

The project paused after Day 5 with twelve open items ([lab notebook](lab-notebook.md#open-items-for-whoever-resumes)).
Item 6 is **nothing checks the evidence.** Most of it is mechanical: no CI step runs a spec's
Verify block, re-runs a `broken:` line, or checks that a ticked criterion's test exists. A script
closes those. What is left after them is a judgment: a `broken:` line shows that a test failed,
not that the break hit what the criterion promised. That judgment has a fixed set of answers,
which is what Jev (TypeSafe AI's decision model, in early access since September 2026) is built
for: typed questions in, a choice and a probability out.

TypeSafe's own claims about speed, cost and accuracy have not been checked independently. So the
plan is an experiment on records that already exist, scored against labels written before the
model runs. It joins the workflow only if it beats the agents the workflow already has, and
catches enough on its own to be worth the step.

| Step | What | Changes the workflow? |
|---|---|---|
| 0 | Close the holes a test or a script can close, including item 6's mechanical half | yes: deterministic fixes |
| 1 | **E1: do the breaks show the test catches what the criterion promised?** | no: offline, on Days 1–5 |
| 2 | Go or no-go on E1, in the lab notebook | no |
| 3 | **Shadow days:** new, minimal days, with Jev asked after each close merges | one records PR per day, nothing else |
| 4 | Decide, in the lab notebook | no |
| 5 | Adopt, if both bars were met: one advisory step | yes: CLAUDE.md change PR |
| later | E2 (mutation survivors), and Jev beside spec-drift, each its own decision | no |

E1 measures how much Jev catches, on seeded hard cases. The shadow days measure false alarms,
errors and cost on live work. A real day has 5–8 criteria, almost all fine, so ten days give too
few bad ones to measure catches; that is why E1 comes first and decides whether the days run.

## Rules Jev never breaks

Borrowed from Redline's Jev plan. Any part of this plan that would break one is out.

1. **Nothing a gate or a drift figure reads.** No test, CI check or `scripts/` gate reads Jev's
   answers, and no figure `spec-drift.py` computes (gap, coverage, Jaccard, removals, hand-offs,
   verification) takes them as input. They live in `experiments/jev/` and
   `docs/dashboard/jev.json` only. The one exception is display: `spec-drift.py` copies
   `jev.json` into its output unread, the way `token_usage()` copies `token-usage.json`, and
   `docs/dashboard/dashboard.js` draws it (see "Jev beside spec-drift").
2. **It only adds review.** Its output can send a bundle to the spec-auditor. It never closes a
   finding, ticks a criterion, skips a step or lets anything pass.
3. **Never in CI.** No call to Jev in a workflow, and no Jev secret in Actions. CI stays
   reproducible.
4. **No deterministic facts.** Test results, line counts, links, names and whether a test exists
   come from code. Jev is never asked them.
5. **Confidence never skips anything.** High confidence bypasses nothing; low confidence means
   "worth a look".
6. **Every call is recorded:** the commit, the bundle's hash, the question's version, Jev's
   version, the answer, the confidence, the recommendation and a timestamp. Errors, timeouts and
   malformed answers give no recommendation, are recorded, and are reported apart: neither a
   flag nor a pass.

## Step 0: deterministic fixes first

Do not give a model a hole that a test can close. Each fix is its own PR, under 400 lines.

- **Open item 6, mechanical half:** a script that, for each ticked criterion, checks the named
  test exists at the commit the closing PR names, runs the spec's Verify block, and re-runs each
  `broken:` line through `scripts/break.py` and compares what it reports. Seen red on a spec with
  a renamed test. E1 runs only on records this script passes, so a model is never credited for
  catching a malformed record.
- **Open item 5:** add non-ASCII and underscore cases for the word rule, in a new file beside
  `tests/contract/` (that directory stays frozen). Seen red with `WORD` set to `[\w']+`.
- **Open item 10:** `scripts/break.py`, or the implementer brief, runs each new test on the code
  as it was before the day, and records that it failed there.
- **Open item 4:** `scripts/invariants.py` fails a rename out of a frozen path and a drop in the
  test count.

**Decided by the maintainer: items 1–3 are knowingly skipped.** These are agent credentials,
check sources and the control plane. Jev adds no autonomy, but the shadow days are more agent PRs
on the holes the Day 5 auditors put first. They stay open, and are not fixed before the first
shadow day. **Why:** this experiment tests Jev as a checker in the workflow, not the workflow's
security. Fixing items 1–3 first would change the conditions the Day 5 audits described, and
nothing in this plan measures that change.

## E1: do the breaks show the test catches what the criterion promised?

### What is judged

The breaks, not the test. A test can assert every promise a criterion makes while its recorded
breaks exercise only some of them. That is incomplete evidence, not a weak test, and E1 asks
only about the evidence.

**The bundle**, identical in the experiment and in adoption: the criterion's text, its test's
source at the commit the closing PR names (not today's, so later changes cannot improve earlier
evidence), and every `broken:` line recorded for it.

**The labels:**

| Label | When | Example |
|---|---|---|
| `supports` | every promise in the criterion has a break that makes the test fail on it | a criterion with one promise and a break that undoes it |
| `insufficient` | at least one promise has no break, even if the test asserts it | C4.1: "stopwords leave the top list, and only it". Both breaks undo the filtering; none touches the counts line, which [the test](../tests/test_cli.py) asserts |
| `contradicts` | a break's report shows the promise false: the test passed, or failed for a reason unrelated to the promise | a `broken:` line whose report is an import error |
| `unrelated` | the break touches nothing the criterion promises | a Day 2 break paired with a Day 4 criterion |

A **promise** is one thing a reader could check apart from the rest. "X, and only X" is two.
Each case in the set lists its criterion's promises, written by the labeller, so a disagreement
can be traced to one of them. The model does not see that list: adoption could not supply it.
Criteria with more than one promise are tagged `compound` and scored apart as well.

The rubric and these examples are committed before the set is built.

### The set

Frozen in `experiments/jev/e1/` before any model sees it, with the commit named in the results.

| Kind | Source | About | Expected label |
|---|---|---|---|
| Real | each criterion and its own `broken:` lines, Days 1–5, that pass Step 0's script | 37 | written by hand, most `supports` |
| Swapped | a `broken:` line paired with another day's criterion | 37 | `unrelated` |
| Insufficient | real breaks that hit only part of a criterion, written by hand | 10–15 | `insufficient` |
| Contradicting | a break whose report shows the claim false | 5 | `contradicts` |

**Labels:** the person who writes a case writes its label and one line of reason. A case they
cannot settle is tagged `ambiguous` and scored on its own, not dropped. Closing-PR decisions are a
reference someone ruled on, not ground truth. Where one is disputed, say so beside it.

### Who answers, from the same bundles

1. Jev.
2. The Opus defect-rater's setup: a fresh agent given only the bundle, asked the same question.
3. A floor: always `supports`. It flags nothing and raises no false alarms, so it sets the false
   alarm count to beat at zero and the catch count at zero.

### Scoring, fixed before the first call

- **A flag** is any answer other than `supports`, or `supports` with probability below **0.9**.
  The threshold is fixed here, not tuned: with 15–20 hard cases, a split into tuning and
  evaluation halves leaves too few on each side to mean anything. The Opus agent states a
  probability the same way.
- **An abstention** counts as a flag: in adoption it would go to the spec-auditor too. The number
  of abstentions is reported beside it. **An error** is neither (rule 6).
- Per label kind, never pooled:
  - On the hand-written `insufficient` and `contradicts` cases: how many are flagged. This is the
    test that counts. Swapped pairs are easy, and a high score on them means little.
  - On real `supports` cases: false alarms. An advisory check that cries wolf gets ignored. This
    count is also what adoption would send to the spec-auditor per day.
  - On `compound` cases: both of the above, apart.
  - Probability against outcome (Brier score, a reliability plot of ten bins): does 0.9 mean 0.9?
  - Cost and time per bundle, measured, not taken from the vendor's figures.

### The bar

All four, or E1 fails:

1. **Useful on its own:** Jev flags at least half of the hand-written `insufficient` and
   `contradicts` cases.
2. **Not noisy:** at most 1 in 10 real `supports` cases flagged.
3. **At least as good:** it flags at least as many hand-written cases as the Opus agent, with no
   more false alarms.
4. **Cheaper:** less cost per bundle than the Opus agent.

Missing the bar on any one is a result, and it gets recorded the same way. If both fail 1 and 2,
the record says the question, not the model, may be the problem.

With about 100 bundles, the result is directional, not proof. Write that next to it.

## Shadow days: the same question on live work

Only if E1 passed. New days, added to `plan.md` as a Phase 2 by their own plan-change PR, which
says nothing about Jev: small features (for example `--lines-only`, `--sort`) that exist to
produce criteria and breaks. Every day runs the full workflow in CLAUDE.md.

- **When:** after the day's closing PR merges, not during it. On fresh `main`, a script
  (`experiments/jev/shadow.py`) sends each ticked criterion of the day to Jev as E1's bundle,
  writes the records, and refreshes `jev.json`. They land in one small PR,
  `day-NN/jev-records`, before the next day's first step.
- **Unseen until the day is merged:** a session that knows a checker is reading writes its
  breaks for the checker, and the measurement is spoiled. Asking after the close merges means no
  answer exists while the day's work, ticks or Notes can still change. The session sees the
  answers when it opens the records PR; later days can learn from them, which is a known limit
  of a shadow run, written next to the result.
- **Every criterion is reviewed, not only the flagged ones:** a fresh spec-auditor run, blind to
  Jev's answers, reads each of the day's bundles and says whether its evidence has a gap. That
  review sets the denominator. Reviewing only the flags would count false alarms but not the
  supported criteria they are a share of, and E1's false alarm rate is a share of supported
  cases. Against it:
  - a flag where the review found no gap is a **false alarm**;
  - a flag where it found a gap is a **catch**, recorded in the next day's Notes like any defect;
  - a gap the review found and Jev did not flag is a **miss**, shown beside the catches.

  This full review is the measurement's cost, not Jev's, and stays out of the cost ceiling
  below. After adoption only the flags are reviewed.
- **The bar, confirmed by the maintainer and written here before the first shadow day.** Until
  then each number is a proposal:

  | Measure | Counted as | Proposed | Why |
  |---|---|---|---|
  | criteria before any rate is read | criteria asked, all shadow days | 40 | about six days; below it, "not enough data yet" |
  | false alarm rate | false alarms ÷ criteria the review found no gap in | at most 1 in 10 | E1's bar, on E1's denominator |
  | escalation rate | flags ÷ criteria asked | at most 1 in 5 | the spec-auditor load adoption would add: one or two bundles on a day of about seven criteria |
  | error rate | errors, timeouts and malformed answers ÷ calls made | at most 1 in 20 | more, and the record has holes |
  | cost per day | Jev's calls, plus the spec-auditor re-runs its flags would cause after adoption | at most the Opus agent's cost per bundle in E1, times the day's criteria | Jev's price is unknown until E1 measures it, so the ceiling is the alternative it must beat |

  Missing any one is a result, recorded the same way.

## Watching Jev on the dashboard

Every existing panel stays as it is. A Jev section is added, built from one committed file,
`docs/dashboard/jev.json`, which only the records PR writes. CI never calls Jev and holds no
secret: it reads the file and builds the page. With no file, the section is hidden, so the
dashboard is unchanged until the experiment starts.

**Publication rule:** the page is built only from `main` (`.github/workflows/dashboard.yml`), and
`jev.json` reaches `main` only through a records PR, which runs only after its day's close has
merged. So the dashboard can never show an answer for a day still open. `shadow.py` refuses a day
whose closing PR has not merged, and a test beside it pins that.

| Panel | Shows | Answers |
|---|---|---|
| E1 results | flagged cases per label kind, for Jev, the Opus agent and the floor, with the bar as a line | did it pass, and where did it fail? |
| Calibration | a ten-bin reliability plot and the Brier score | does 0.9 mean 0.9? |
| Shadow days | per day: criteria asked, flags, false alarms, catches, misses, errors, cost, time | what did each day cost and find? |
| Running rates | false alarm, escalation and error rates over days, each on its denominator in the shadow bar and against its threshold | is it still inside the bar? |
| Recent calls | the last 20 records: criterion, answer, confidence, Jev version, outcome | why did it say that? |

Each panel carries the caveat "a model's judgment; see its scored accuracy".

## Jev beside spec-drift

`spec-drift.py` measures drift by names. Its own caveats say so: "They match names, not meaning:
prose is not understood, so a spec can name a thing the code has and still describe it wrongly."
Gap, coverage and Jaccard can all look healthy while the code no longer does what a spec says.
That is a question of meaning with fixed answers, which is where Jev could add a reading.

| Use | Question | Answers | Comes |
|---|---|---|---|
| Evidence drift | do the day's breaks support its ticked criteria? (E1's question) | share per day | free with the shadow days |
| Hand-off resolution | does this later spec or PR do what hand-off H4.1 deferred? A citation of the ID shows only that it was named | done / partly / not | after the shadow days |
| Meaning drift | does the code at this merge still do what this criterion or premise says? | holds / no longer holds / unclear | last: it is scored on E2's survivors |

- **The drift figures stay independent** (rule 1). `spec-drift.py` never calls Jev (rule 3) and
  computes nothing from `jev.json`: a new `jev()` loader, beside `token_usage()`, copies the file
  into the output under its own `jev` key, unread. `docs/dashboard/dashboard.js` draws these
  series, labelled as model output, in the Jev section, never on the gap, coverage or Jaccard
  charts. A test in `scripts/test_spec_drift.py` pins it: every figure except `jev` is the same
  with and without `jev.json`.
- **Meaning drift is asked only where no test answers:** criteria with no test, and premises in a
  spec's prose (rule 4). And only for those whose code files changed that day: asking every
  earlier criterion at every close grows with the square of the days.
- **No series is shown before it is scored.** Each use gets its own small labelled set, as E1
  did. A mutant from E2 that passes every test but breaks a criterion is meaning drift by
  definition, so E2's survivors are the set for that use.

## E2, later: does a surviving mutant break the criterion?

Not part of this plan. It is decided after the shadow days, in its own plan-change PR, and only if E1 showed
this kind of judgment gives a usable signal. Running the code answers "would the tests catch this
mutant?". It cannot answer whether a mutant that survives breaks what the plan wants, or behaves
the same as the original. `[\w']+` is that case: every contract test passes, and only `plan.md`'s
rule shows it is wrong.

If it is taken up, its plan must state, before any run:

- **A named, finite operator set**, for example: swap a comparison, change a constant by one,
  drop a negation, swap `and`/`or`, delete one statement, swap one regex character class. Not
  "every single-point mutant": arbitrary replacements have no end.
- **The pinned revision and environment:** the commit of `wordtally/` and `tests/`, and the
  Python version.
- **Outcomes kept apart:** killed by an assertion, killed by an error, invalid (does not import or
  parse), timed out, survived. Only survivors are labelled.
- **Its own bar,** as E1's, and a minimum of each class: at least 5 `violates` and 5 `equivalent`
  survivors, or it is recorded as "too few to judge" rather than scored. Without `equivalent`
  cases, false alarms cannot be measured.

## Not in this plan, and why

- **Choosing which mutation to run next:** ranking only pays when there are too many mutants to
  run them all. Here every mutant runs in seconds.
- **Picking which lessons to remind the implementer of:** the notebook found that lessons changed
  behaviour only once they became a rule or a script. About a dozen are left, so sending all of
  them costs little, and five days cannot show fewer repeated mistakes.
- **Predicting `new` or `hold` from a criterion's text:** the tag depends on the code before the
  day, which the text does not hold.
- **Choosing a model per track:** the Haiku implementer is the maintainer's choice.
- **Replacing a deterministic check:** tests, `break.py`, `pr-names.py`, the 400-line gate,
  `invariants.py` and Step 0's evidence script stay as they are. A probability on a fact makes it
  weaker.
- **Review time in the cost:** five days cannot measure it. The false alarm count stands in for
  it: each is one bundle the spec-auditor reads.

## Step 5: adoption, if both bars were met

Only as advice. The question, the bundle and the threshold stay as E1 and the shadow days used
them; what changes is when Jev is asked and who sees the answer:

- **Calls and review move before the merge.** At the close, after Step 0's evidence script
  passes and before the defect-rater, each criterion goes to Jev as the same bundle E1 scored:
  its text, its test at the closing commit, and its `broken:` lines. A flag, as E1 defines it and
  at E1's threshold, sends the bundle to the spec-auditor, and the closing PR records both. The
  session sees the answers while the day is open; that is the point of advice, and why the
  shadow days had to come first, while it could not.
- **It never blocks a merge;** the maintainer decides.
- **Publication stays after the merge.** The records still reach `main` through a
  `day-NN/jev-records` PR once the close has merged, and only that PR writes `jev.json`, so the
  publication rule and the dashboard panels are unchanged.

Adoption is a CLAUDE.md change PR that names the step, the threshold and the experiment it rests
on. If a later day shows the threshold wrong, it changes the same way.

## Ground rules

- The rubric, labels, sets, threshold and bar are committed **before** the first model call; the
  commit is named in the results. Nothing is relabelled after seeing a model's answer, except as a
  recorded correction.
- Jev and the Opus agent never see execution outcomes beyond what the bundle states, and never
  each other's answers.
- Bundles are sent to TypeSafe's API. The repository is public, but the experiment sends only
  what is already committed: no transcripts and no memory files.
- Experiment code stays in `experiments/`, outside `wordtally/`, `tests/` and CI. A test of the
  experiment's own scripts goes in `experiments/`, beside them. Step 0's evidence script is not
  experiment code: it goes in `scripts/`.
- Results go in a new lab-notebook entry with its own measurement table, including what failed.

## Order of work

Each step is a PR under 400 lines, branched from fresh `main`, and waits for "merged".

1. This plan.
2. Items 1–3, or the record that they were skipped (the open decision under Step 0).
3. Step 0, one PR per open item (6's mechanical half, 5, 10, 4).
4. E1 rubric, set and labels, with the script that builds the swapped pairs and pins each test
   to its closing commit. No model calls.
5. E1 runner (`experiments/jev/run.py`), with the per-call records, and results.
6. E1's go or no-go, in the lab notebook. On no-go, stop here and record why.
7. The Jev dashboard section: `jev.json`, and the panels E1 can already fill.
8. The shadow bar written into this plan, and the Phase 2 plan-change PR to `plan.md`.
9. The shadow days, each under CLAUDE.md's full workflow, each followed by its records PR once
   the close has merged.
10. The decision, in the lab notebook. Then, only if both bars were met, the adoption PR.
11. Hand-off resolution, E2, and meaning drift beside spec-drift, each its own decision.

## What is needed

- Jev early access and an API key, kept out of the repository (an environment variable).
- TypeSafe's documentation for the request shape: how a question's type, answers and probability
  are declared. The [documentation](https://docs.typesafe.ai/introduction) recommends small,
  single-point questions and breaking up questions that turn on several factors. E1 asks one
  question per bundle, and scores `compound` criteria apart to see whether that holds.
- The maintainer's time to write the rubric and to write and label 15–20 hand-made cases. This
  is the cost that matters: without it there is nothing to score against.
- For the shadow days: the maintainer's time to merge each day's PRs, as before.
