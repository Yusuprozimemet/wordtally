# wordtally

A command-line word counter in Python, standard library only:

```
python -m wordtally [--top N] [--stopwords] [--json] [FILE...]
```

It prints the lines, words and characters of each file, as `wc` does, and a total line when more
than one file is named. With no file, or `-`, it reads standard input. `--top N` lists the N most
frequent words, `--stopwords` leaves common English words out of that list, and `--json` prints
the same counts as one JSON object. A word is a run of letters, digits and apostrophes.
[plan.md](plan.md) is the plan it was built to; all five days are done.

The project is built one day spec at a time by Claude Code sessions, with a maintainer who merges
every pull request, and is the pilot of the agentic workflow kit (github.com/Yusuprozimemet/agentic-workflow-kit).
[CLAUDE.md](CLAUDE.md) gives the working order, [specs/README.md](specs/README.md) the spec rules,
and [docs/workflow.md](docs/workflow.md) draws it. The dashboard is on
[GitHub Pages](https://yusuprozimemet.github.io/wordtally/).

## Status

Paused after Day 5, 2026-10-28. The plan is delivered; the end-of-project audits and what they
left open are in the [lab notebook's Retrospective](docs/lab-notebook.md#retrospective). Work
resumes only under a new plan.

## Findings

- Every day's estimate held (3 pull requests each), and the frozen word-rule tests were never
  edited.
- A lesson written only in a day's Notes did not reach the next day: the same gap recurred
  (Days 4 and 5). Behaviour changed only where a lesson became a rule or a script.
- "Nothing merges without the maintainer" is enforced by instructions, not by GitHub: the agent
  works with the owner's admin credentials. Fix that before giving agents more autonomy.

## Running the tests

```
python -m unittest discover -s tests -t .
```

The dashboard's own tools and their tests are in `scripts/`; they need Python with `numpy`,
`node` for the page tests, and `gh`, logged in.
