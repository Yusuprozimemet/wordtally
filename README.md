# wordtally

A command-line word counter in Python, standard library only:

```
python -m wordtally FILE...
```

It prints the number of words in each file. A word is a run of letters, digits and apostrophes.
[plan.md](plan.md) says where it is going.

The project is built one day spec at a time by Claude Code sessions, with a maintainer who merges
every pull request, and is the pilot of the agentic workflow kit (github.com/Yusuprozimemet/agentic-workflow-kit).
[CLAUDE.md](CLAUDE.md) gives the working order, [specs/README.md](specs/README.md) the spec rules,
and [docs/workflow.md](docs/workflow.md) draws it. The dashboard is on
[GitHub Pages](https://yusuprozimemet.github.io/wordtally/).

## Running the tests

```
python -m unittest discover -s tests -t .
```

The dashboard's own tools and their tests are in `scripts/`; they need Python with `numpy`,
`node` for the page tests, and `gh`, logged in.
