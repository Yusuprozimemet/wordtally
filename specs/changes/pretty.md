# Pretty JSON output

## What changes
`--json` currently emits one compact line. `--json --pretty` emits the same object indented by two spaces. `--pretty` without `--json` is a usage error.

## Why
Indented JSON is easier to read in a terminal while compact output remains available for scripts.

## Acceptance criteria
- [x] S-pretty.1 **new** — `--json --pretty` emits the same JSON object with two-space indentation, including totals and top words. Test: `tests.test_cli.CliTest.test_pretty_json`.
      Red today: the CLI rejects `--pretty`.
- [x] S-pretty.2 **new** — `--pretty` without `--json` exits 2 with a usage error and no output. Test: `tests.test_cli.CliTest.test_pretty_requires_json`.
      Red today: the CLI does not explain that `--pretty` requires `--json`.
- [x] S-pretty.3 **hold** — `--json` alone keeps its compact output. Test: `tests.test_cli.CliTest.test_json_prints_the_counts_as_one_object`.
      broken: compact JSON is indented ? AssertionError: Tuples differ

## Verify
```bash
python -m unittest discover -s tests -t .
python scripts/track-red.py --branch change/pretty
```
