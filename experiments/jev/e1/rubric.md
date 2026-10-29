# E1 rubric: do the breaks show the test catches what the criterion promised?

<!-- Committed before the set is built and before any model call (docs/workflow-improvement-plan.md,
"Ground rules"). A change after the first call is a recorded correction, never a silent edit. -->

## The question, version 1

Asked once per bundle, the same words for every answerer:

> Here is an acceptance criterion, the source of the check that tests it, and the `broken:`
> lines recorded for it: each one a change made on purpose and what the check reported with it
> in. Judge the breaks, not the check: do they show the check catches what the criterion
> promises? Answer one of `supports`, `insufficient`, `contradicts`, `unrelated`, and the
> probability that your answer is right.

## The bundle

The criterion's text up to its first `Evidence:` or `broken:` line; the check's source at the
commit the day's close merged (each test method a `broken:` line runs or the criterion names,
with its file's module-level helpers, and each `broken:` command that is not a test); and every
`broken:` line, with the notes in parentheses recorded beside them. Nothing else: no promises
list, no label, no day, no PR.

## The labels

| Label | When |
|---|---|
| `supports` | every promise in the criterion has a break that makes the check fail on it |
| `insufficient` | at least one promise has no break, even if the check asserts it |
| `contradicts` | a break's report shows the promise false: the check passed, or failed for a reason unrelated to the promise |
| `unrelated` | the break touches nothing the criterion promises |

A near miss, a break recorded as passing by design, counts for the exemption it shows (the line
of a test that may go), not as a break of a promise.

## Promises

A promise is one thing a reader could check apart from the rest. The labeller counts them from
the criterion's headline, the words between the tag and the first colon: "X, and only X" is two,
"A and B" is two, a single behaviour is one. The exact output and exit status in the body are
how the headline is checked, not promises of their own. The one exception is a `hold` whose body
names two separate checks (the suite passes, and a diff prints nothing): each is a promise.

A criterion with more than one promise is tagged `compound`. A case the labeller cannot settle
keeps its best label, is tagged `ambiguous` with the reason, and is scored on its own.

## Kinds

| Kind | Built from | Label |
|---|---|---|
| `real` | a ticked criterion of Days 1–5 and all its own `broken:` lines, if `scripts/evidence.py` passes every one | by hand |
| `swapped` | one `broken:` line paired with a criterion of another day, chosen by `build.py`'s rule | `unrelated` |
| `insufficient` | a `real` criterion with only some of its own breaks, so that a promise has none | by hand |
| `contradicts` | a `real` criterion with one break's report rewritten to show the promise false | by hand |

Every hand label in `cases.json` was drafted by Claude (`"by": "claude"`) and ruled on by the
maintainer in the PR that added it; a label the maintainer changed says so in its reason.
