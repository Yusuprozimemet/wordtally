# Add --version

## What changes
`python -m wordtally --version` prints the package version and exits successfully.

## Why
Users can identify the installed version from the command line.

## Acceptance criteria
- [x] S-version.1 **new** ? `python -m wordtally --version` prints exactly "wordtally 0.1.0" and exits 0. Test: `CliTest.test_version_prints_version_and_exits`.
      Red today: the option is unrecognized and exits 2.
- [x] S-version.2 **hold** ? counting standard input with no flags is unchanged. Test: `CliTest.test_no_file_reads_standard_input`.
      broken: stdin read returns empty bytes ? AssertionError: Tuples differ: (0, '0 0 0 -\n') != (0, ' 2  3 12 -\n')

## Verify
```bash
python -m unittest tests.test_cli
```
