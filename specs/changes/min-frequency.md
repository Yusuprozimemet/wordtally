# Minimum frequency for top words

## What changes
`--min-frequency N` limits the `--top` list to words counted at least N times, in both plain and JSON output. N is a whole number of at least 1. Without `--top`, the option is a usage error. Counts, ordering, the top limit and stopword filtering otherwise retain their existing meanings.

## Why
A frequency threshold lets users omit rare words from the top list.

## Acceptance criteria
- [x] S-min-frequency.1 **new** — With `--top`, the threshold filters the top words in plain and JSON output, including an empty JSON list when none qualify; stopwords remain excluded and ties remain alphabetical. Test: `tests.test_cli.CliTest.test_min_frequency_filters_plain_and_json_top`.
      Red today: the CLI rejects `--min-frequency`.
- [x] S-min-frequency.2 **new** — `--min-frequency` without `--top` exits 2 with a usage error and no standard output. Test: `tests.test_cli.CliTest.test_min_frequency_requires_top`.
      Red today: the CLI does not explain the dependency.
- [x] S-min-frequency.3 **new** — N must be a whole number of at least 1; invalid values exit 2 with a usage error and no standard output. Test: `tests.test_cli.CliTest.test_min_frequency_requires_positive_whole_number`.
      Red today: the CLI does not report the number requirement for this option.
- [x] S-min-frequency.4 **hold** — `--top` without the option keeps its existing output. Test: `tests.test_cli.CliTest.test_top_lists_the_most_frequent_words_after_the_total`.
      broken: top words sorted by ascending frequency → AssertionError: Tuples differ

## Verify
```bash
python -m unittest discover -s tests -t .
python scripts/track-red.py --branch change/min-frequency
```
