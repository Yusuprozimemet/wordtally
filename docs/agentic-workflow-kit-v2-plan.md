# Agentic workflow kit v2 plan

Written 2026-10-29. Planning only: implementation belongs in
`C:\Users\HackYourFuture\yusup\agentic-workflow-kit`. This document does not resume
Wordtally's feature work, delete its application, or change the kit.

## Decision

Build v2 in the existing kit repository. Use Wordtally's newer tools and dashboard,
the kit's current starter documents and defaults, and the fixes unique to each side.
Keep the kit's Git history and all of `kit/`, including its source records, lessons,
examples and validation tools. Wordtally remains the worked example.

Assemble and validate the candidate in a separate checkout or scratch repository.
Deliver one kit PR with commits grouped by purpose. Projects created from v2 still
start from an export without `kit/`, with their own fresh history on `main`.

This approach keeps the newer dashboard components together and reuses the work
already done to make the kit's documents reusable. Commit counts are context, not
proof of compatibility; select changes by their behavior and tests.

## Inspected sources and limits

| Source | Revision | Use |
|---|---|---|
| Wordtally | `82b4ce7c254e768c3e25c90832021b1e6beff4f0` | New tooling, dashboard and generic workflow lessons |
| Current kit | `6418ac3bd96363bc538b83ad61984affd0450116` | Destination baseline, templates, kit records and kit-only fixes |
| Wordtally's initial snapshot | `df0c205` | Check what Wordtally actually inherited |
| Kit before Wordtally started | `563fc31db040fb16afbed6e6fb7ef7c90acd2674` | Candidate file-level common base; verify each file against the initial snapshot |

These are local revisions inspected for this plan. At implementation time, refresh
the comparison if either branch has advanced. The repositories have separate
histories; do not assume `git merge-base` can identify the copy's origin.

A count of non-merge commits since the two starting snapshots, limited to
`scripts/`, `docs/dashboard/`, `.github/` and `.claude/`, gives 29 for Wordtally and
9 for the kit. Different path selections give different counts. The kit's nine
commits are already in the destination: preserve their changes rather than
cherry-picking them into the same repository again.

Earlier verification copied the auditor guard, seen-red helper, invariants changes
and token script into a temporary kit. Their four script test suites passed 35
tests. This was a limited compatibility check, not validation of the complete v2
or the separate Windows long-path test under `tests/`.

## File sources

| Files | Starting point and treatment |
|---|---|
| `scripts/` | Wordtally's newer functionality; classify each shared file before replacing it. Preserve the union of both test suites. |
| `scripts/break.py`, `scripts/test_break.py` | Keep the current kit versions, including output assertions, command-not-run refusal and temporary-path cleanup. |
| `scripts/spec-drift.py`, `scripts/test_spec_drift.py` | Three-way merge shared changes; retain both sets of regressions and the kit's fixture hooks. |
| `scripts/invariants.py`, `scripts/test_invariants.py` | Copy Wordtally's pair; the kit versions were unchanged from the starting snapshot. Keep project-specific protection rules out of defaults. |
| `scripts/token-usage.py` | Copy Wordtally's version; retain kit tests and add the long-path regression below. Verify old token rows remain readable. |
| `tests/test_token_usage.py` | Move its useful regression into `scripts/test_token_usage.py`, adapting relative paths. Do not create an app `tests/` directory just for this test. |
| `docs/dashboard/dashboard.js`, `index.html`, `dashboard.css` | Start with Wordtally's coordinated display changes, merge kit-only fixes, and generalize project-specific text. Review all three files together. |
| `.claude/settings.json` | Copy Wordtally's auditor hook wiring, after confirming no destination settings would be overwritten. |
| `.github/workflows/pr-checks.yml`, `spec-drift-tests.yml` | Merge deliberately: retain kit configuration and check names, add tooling tests, and make Python-specific enforcement opt-in. |
| `.github/workflows/dashboard.yml`, `.github/workflows/README.md` | Content already matches after normalizing line endings; retain and update documentation only where behavior changes. |
| `.github/workflows/tests.yml` | Do not copy Wordtally's app-test job. New projects supply their own application test workflow. |
| `CLAUDE.md`, `README.md`, all seven `.claude/agents/*.md`, `specs/README.md`, `specs/_template.md`, `docs/workflow.md`, `.github/pull_request_template.md` | Use current kit templates; add only missing generic lessons and instructions. Preserve `<!-- PROJECT: ... -->` placeholders. |
| `plan.md`, `docs/lab-notebook.md`, `spec-drift.config.json` | Keep the kit's starter versions. Document optional new settings without importing Wordtally's rules or results. |
| `.gitattributes`, `.gitignore` | Retain kit conventions and add relevant generic exclusions, including `.env` and generated dashboard output/cache. |
| `kit/` | Preserve existing contents. Update `SOURCE.md`, `CHANGES.md`, starter validation and reviewed dashboard comparison baselines. |

Exclude Wordtally's application, application tests, completed day specs,
`specs/breaks/`, experiments and results, and its project-specific improvement plans.
Reference the pinned Wordtally revision from the kit's source record instead of
copying those records into the starter. Export tracked files from pinned revisions;
do not copy local `.env`, caches, transcripts, `.git`, or untracked output.

## 1. Record the baseline and assemble the candidate

1. Begin in the kit workspace on a dedicated branch, for example
   `tooling/kit-v2`. Inspect working-tree changes before preparing an isolated copy.
2. Record the source revisions and baseline test results, including
   `kit/starter-check.py` and `kit/compare-page.py`.
3. Make a file manifest recording each candidate's source, source revision and
   treatment: retain, copy, merge, reset or exclude. Compare Git blobs or normalize
   line endings for classification; CRLF alone is not a functional difference.
4. Use the current kit tree as the container, preserving `kit/`. Apply the selected
   Wordtally files and merges according to the table. Avoid whole-directory
   replacements of `.github/`, `.claude/` or `docs/dashboard/`.

Exit condition: every changed or added file has a source and purpose, and no
Wordtally application or runtime data has entered the starter.

## 2. Preserve both sides' behavior

For a shared file changed on both sides, verify its common-base contents, then use
`git merge-file` with the current kit file, base file and Wordtally file in that
order. Resolve conflicts by behavior and test coverage. A clean textual merge still
requires review. If initialization already changed a file, establish that file's
base separately instead of assuming the entire initial snapshot is unchanged.

Keep the kit's following behavior, whether it is already present in Wordtally or
needs to be restored:

- `break.py` output expectations, refusal when execution never started, and path
  normalization; run the imported `seen-red.py` and `evidence.py` tests against it.
- Spec drift excludes the spec rules and template from measured spec content;
  recognizes Python test classes and skip forms; interprets course-correction
  headings; avoids counting a hand-off citation as a new hand-off; and reads
  provenance before the first commit without throwing.
- Dashboard single-row and no-PR handling, finite axis labels, bounded merge strips,
  singular/plural wording, dynamic dates, generic labels and table-heading styles.
- `JIRA_KEY` repository-variable wiring and its regression tests.

Keep Wordtally's production-name coverage and match paths, exclusion of `specs/`
from the code corpus, shuffle-band explanations, evidence report and staleness
display, relabel agreement, token breakdown by agent, stronger invariants and
auditor hooks. Preserve cache invalidation for changed metric definitions.

Check token-data compatibility explicitly: the kit fixture can contain older rows
without an `agent` field, while Wordtally's `--merge` currently reads that field
directly. Define an explicit unknown attribution for older rows and preserve their
counts; do not invent which agent spent them.

Exit condition: both sets of regression tests remain represented, with any
intentional behavior change recorded in `kit/CHANGES.md`.

## 3. Reset project state and document supported runners

- Keep `docs/dashboard/token-usage.json` as `[]`.
- Omit `docs/dashboard/evidence-checks.json` until a project generates a report.
  The reader already has a missing-report state; an arbitrary `{}` or `[]` is not
  a valid evidence report and must not appear as a passing run.
- Exclude generated `spec-drift.json` and `.spec-drift-cache.json` from the export.
- Keep empty service, infrastructure, renamed/moved-path and frozen-file settings.
  Leave `test_count` absent by default and document its optional configuration.
- Preserve `specs/README.md` and `specs/_template.md`, with no completed day specs
  or break manifests in the starter.

The kit remains usable beyond Python. `seen-red.py` accepts a command but copies
changed files from `tests/`; `track-red.py` discovers and runs Python `unittest`
tests; `evidence.py` has Python-specific named-test lookup and its own Verify/break
conventions. Describe those limits in setup instructions.

Keep these tools and their self-tests. For v2, make the PR enforcement step for
`track-red.py` opt-in through a documented repository variable
`TRACK_RED_RUNNER=unittest`. Unset means enforcement is not configured; an
unsupported nonempty value reports a configuration error. The job should still
report its status, and the tooling's self-tests must run independently of that
setting. Other languages keep the seen-red workflow rule and supply their own
test command; adding general runner adapters is a separate change.

Exit condition: a new project has no inherited results or mandatory application
test runner, and a Python project can explicitly enable the existing track check.

## 4. Update starter instructions and CI together

Start from current kit documents. Several lessons, including "One session per
step" and the implementer brief, are already present; compare before adding them.
Port missing auditor-hook instructions, seen-red usage, post-merge audit timing,
and generic pitfalls. Replace Wordtally-specific commands and paths with examples
or placeholders. Describe the guard's actual limits: it blocks recognized commands
and detects certain repository changes; it is not a complete read-only sandbox.

Remove Wordtally-specific day commentary from the dashboard, including the relabel
panel's Day 1/Day 3 explanation. Explain absent data in general terms. Keep the
distinction between vocabulary measurements, recorded evidence and correctness.

In CI:

- Run every retained `scripts/test_*.py`, including the evidence, seen-red,
  track-red and auditor tests and the relocated token regression.
- Cover all files those tests depend on in change detection: scripts/tests,
  dashboard HTML/CSS/JS, agent files, settings, config and the relevant kit checks
  and fixtures. Adding a run step without its trigger paths is incomplete.
- Preserve existing required-check names and the always-reporting gate behavior.
  Include the starter job in the dashboard test gate when `kit/` is present; the
  starter step remains safely skipped in exported projects without `kit/`.
- Preserve dashboard publishing configuration and optional `JIRA_KEY` support.
  Document the opt-in track runner and the requirement for each new project to
  provide its own application test workflow.
- Exercise the Windows token-path regression on Windows as well as running the
  tooling suites in Linux CI.

Exit condition: the instructions match the default and optional CI behavior, and
changes to any new tool can actually trigger its tests.

## 5. Validate the kit and an exported starter

Run these checks against the exact candidate to be reviewed. Record versions and
results rather than copying old test counts. Local prerequisites include Python,
NumPy, PyYAML, Git, Node, the `gh` executable and the shell used by replay tests.

| Check | Passing result |
|---|---|
| Full tooling suite | Execute every `scripts/test_*.py` script and fail on a nonzero exit; imported tools work with the kit's `break.py`. |
| Windows regression | The retained long-path test reaches a transcript beyond MAX_PATH and counts both main and subagent usage. |
| Kit dashboard fixtures | Old source-project data and new coverage/evidence/token fixtures draw without exceptions or invalid numeric labels. Missing optional fields remain supported. |
| Data compatibility | Legacy token rows, absent evidence, valid reports, stale reports and malformed reports have the documented distinct outcomes. |
| Fresh starter | Export candidate HEAD without `kit/`, initialize `main`, make one commit, keep no remote, and run `spec-drift.py --build` through `kit/starter-check.py`. |
| Starter rendering | The built page draws in the Node harness with no unexpected errors, failed panels, `NaN`, `Infinity` or `undefined`; new panels show truthful empty states. |
| Before the first commit | Preserve the kit's targeted provenance regression: no HEAD produces a null commit rather than an exception. This is distinct from promising a full dashboard build without history. |
| Generic starter | No application files, completed day specs, results, local settings or unacknowledged source-project references remain. Placeholder docs and local links are usable. |
| CI applicability | Unconfigured projects do not run Python application discovery; opted-in Python tracks enforce red-on-base/green-on-head and reject unreadable criteria, errors and zero-test runs. |
| Visual review | Inspect an empty starter and a populated fixture at desktop and narrow widths; verify the new panels, labels, overflow and missing-data messages. |

`kit/starter-check.py` archives **HEAD**, not uncommitted edits. Commit the prepared
candidate locally before that check; rerun relevant checks after later changes.

Extend its reference scan to cover Wordtally and its URLs as well as the original
source project. Prefer moving historical records under `kit/`; retained lessons
must be clearly attributed. Review existing broad exemptions so a source-project
path in an active instruction cannot hide inside an exempt document.

Run `python kit/compare-page.py` before updating its saved hashes. List and inspect
the changed, new and removed boxes; v2 intentionally changes some panels. Only
after that review run `--write`, then rerun the comparison and full affected page
tests. Updating hashes alone does not demonstrate compatibility.

Exit condition: the candidate works as both the maintained kit and a clean export,
and the new displays work on empty and populated data.

## 6. Deliver one reviewable kit PR

Use separate commits for tooling integration, dashboard integration, and starter
docs/defaults/validation. Preserve intermediate source attribution in
`kit/SOURCE.md` and add the v2 decisions, limitations and results to
`kit/CHANGES.md`. Keep historical entries intact.

The PR description should contain the source revisions, file-source summary,
retained kit-only fixes, changed dashboard boxes, test results, fresh-starter
result and opt-in runner behavior. The kit enforces a 400-changed-line limit;
measure the final diff. If it exceeds that limit, use its existing documented
`Oversized:` mechanism with a concrete explanation of why this coordinated v2
update is reviewed together. Do not silently disable the limit.

Completion means the PR is ready for review with the checks above passing. Merging,
publishing and creating projects from the kit are later actions. This plan makes
no changes to repository settings or to Wordtally beyond recording the plan.

## Implementation handoff

Start in the existing `agentic-workflow-kit` workspace. Read its current working
instructions and this plan, verify the pinned sources, then prepare v2 on a branch
using an isolated checkout. Keep `kit/` and history, use Wordtally for newer tools
and dashboard features, use current kit templates/defaults, preserve both sides'
fixes, and validate the export from candidate HEAD. Prepare the PR without merging.
