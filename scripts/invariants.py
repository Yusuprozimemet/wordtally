"""Fail a pull request that edits what the project must not change, and name each file.

The frozen files are the project's safety net: applied migrations, which are never changed once
they have run, and the tests that prove the behaviour a change has to keep. The project file,
spec-drift.config.json at the root, lists them as regular expressions over the path (`frozen`),
read as the base has it, so a pull request cannot unfreeze what it edits; none, and nothing is
frozen. Additions and pure renames pass, so a move stays possible; a modification, a deletion, a
type change or a rename with an edit fails. Reads the same three-dot diff as the size check in
pr-checks.yml.

    python scripts/invariants.py <base> <head>
"""
import json
import re
import subprocess
import sys

CONFIG = "spec-drift.config.json"
WORDS = {"M": "modified", "D": "deleted", "T": "type changed"}


def frozen_patterns(base):
    """The project file's `frozen` patterns at base; none with no file or no field."""
    shown = subprocess.run(["git", "show", f"{base}:{CONFIG}"], capture_output=True, text=True, encoding="utf-8")
    if shown.returncode:
        return ()
    return tuple(re.compile(p) for p in json.loads(shown.stdout).get("frozen", []))


def protected(path, patterns):
    return any(p.search(path) for p in patterns)


def entries(name_status_lines):
    """(code, status, similarity, old path, new path) per line of `git diff --name-status -M`."""
    for line in name_status_lines:
        if not line.strip():
            continue
        fields = line.split("\t")
        code = fields[0]
        new = fields[2] if len(fields) > 2 else fields[1]
        yield code, code[0], int(code[1:] or 100), fields[1], new


def violations(name_status_lines, patterns):
    """One line per protected file that is modified, deleted, retyped or renamed with an edit."""
    found = []
    for code, status, _, old, new in entries(name_status_lines):
        if status == "R" and code != "R100" and protected(old, patterns):
            found.append(f"renamed with an edit ({code}): {old} -> {new}")
        elif status in WORDS and protected(old, patterns):
            found.append(f"{WORDS[status]}: {old}")
    return found


def passed(name_status_lines, patterns):
    """How many protected files the diff adds or moves as they are: the count the OK line prints."""
    count = 0
    for code, status, _, old, new in entries(name_status_lines):
        if status == "A" or status == "C" or code == "R100":
            count += protected(old, patterns) or protected(new, patterns)
    return count


def main(argv):
    if len(argv) != 2:
        print("usage: python scripts/invariants.py <base> <head>", file=sys.stderr)
        return 2
    base, head = argv
    diff = subprocess.run(
        ["git", "diff", "--name-status", "-M", "-l0", f"{base}...{head}"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if diff.returncode:
        print(diff.stderr, file=sys.stderr)
        return 2
    patterns = frozen_patterns(base)
    if not patterns:
        print(f"Nothing frozen: {CONFIG} sets no `frozen` patterns.")
        return 0
    lines = diff.stdout.splitlines()
    found = violations(lines, patterns)
    if found:
        for line in found:
            print(line)
        print("These files are frozen: add a new migration instead of editing an applied one. "
              "A frozen test edit means stop and ask (see CLAUDE.md).")
        return 1
    print(f"OK: no frozen file was modified, deleted or renamed with an edit "
          f"({passed(lines, patterns)} frozen files added or moved unchanged).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
