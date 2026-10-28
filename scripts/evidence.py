"""Each ticked criterion's evidence holds up at the commit its day's close merged.

    python scripts/evidence.py specs/day-05-json.md [...] [--ref main]

For each spec, at the merge commit of its day's close (`day-NN/close-the-day`) on --ref:

- every test a ticked criterion names (`CliTest.test_name`) is defined there, in a class of that
  name under tests/;
- every line of the Verify block runs, with bash, in a scratch worktree at that commit, and gives
  what its comment says. A comment is a list split at ", ", a trailing "(...)" dropped: "nothing"
  wants no output, "exit N" that exit status, and anything else a line of output that is it or
  starts with it and a space. A line with no comment wants exit 0. `main` in a line means the
  close's first parent, so a line written as `git diff main` reads the day's base, not today's;
- every `broken:` line under a ticked criterion re-runs through scripts/break.py, from the
  arguments recorded for it in specs/breaks/day-NN.json, and reports what the line says, temporary
  directory names aside, and a report pasted across lines or with its backslashes undoubled read
  as the escapes break.py printed. A `broken:` line with no recorded arguments fails: prose cannot
  be re-run.

The breaks file is a list of {"what", "file", "find", "replace", "command"}, "what" being the text
of the `broken:` line before its last arrow, "file" a path from the repository root, and "command"
an argument list run from that root, `bash` meaning Git's bash on Windows.

Item 6 of the lab notebook's open items: no step checked the evidence a close ticks a box on. It
prints one line per check and exits 1 if any failed. It changes no file outside the worktree.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BREAK = os.path.join(HERE, "break.py")

CRITERION = re.compile(r"^- \[([ x])\] (C\d+\.\d+)\b")
TEST = re.compile(r"`(\w+)\.(test_\w+)`")
# At the last arrow: Day 1 recorded two breaks with an arrow inside what was broken.
BROKEN = re.compile(r"^\s*broken: (.+) → (.*)$", re.S)
PR_SUFFIX = re.compile(r"\s+\(#\d+\)$")
TEMP_NAME = re.compile(r"tmp[0-9a-z_]{8}")
COMMENT = re.compile(r"^(.*?)\s{2,}#\s*(.*)$")


def git(*args, check=True):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=check).stdout


def close_commit(day, ref):
    """The latest merge on ref of the day's close branch, or None."""
    merge = re.compile(rf"^Merge pull request #\d+ from \S+/day-{day}/close-the-day(?:-\S*)?$")
    for line in git("log", "--merges", "--first-parent", "--format=%H %s", ref).splitlines():
        sha, subject = line.split(" ", 1)
        if merge.match(subject):
            return sha
    return None


def criteria(text):
    """{id: lines} for each ticked criterion under Acceptance criteria."""
    found, current, inside = {}, None, False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Acceptance criteria"
            current = None
            continue
        if not inside:
            continue
        m = CRITERION.match(line)
        if m:
            current = m.group(2) if m.group(1) == "x" else None
            if current:
                found[current] = []
        elif line.startswith("- "):
            current = None
        if current:
            found[current].append(line)
    return found


def verify_lines(text):
    """The commands of the Verify block's first fenced block."""
    block = re.search(r"^## Verify\s*\n```\w*\n(.*?)^```", text, re.M | re.S)
    return [l for l in block.group(1).splitlines() if l.strip()] if block else []


def test_exists(commit, cls, name):
    hits = git("grep", "-l", "-E", rf"^class {cls}\b", commit, "--", "tests", check=False).split()
    for hit in hits:  # <commit>:<path>
        if re.search(rf"^\s+def {name}\(", git("show", hit), re.M):
            return True
    return False


def bash():
    """Git's own bash on Windows: the first bash on PATH there may be WSL's, which cannot run git."""
    if os.name == "nt":
        root = os.path.dirname(shutil.which("git") or "")
        while root and os.path.dirname(root) != root:
            if os.path.isfile(os.path.join(root, "bin", "bash.exe")):
                return os.path.join(root, "bin", "bash.exe")
            root = os.path.dirname(root)
    return shutil.which("bash") or "bash"


def expected(comment, code, output):
    """Why the output is not what the comment says, or None."""
    lines = [l.strip() for l in output.splitlines()]
    for part in re.sub(r"\s*\(.*\)$", "", comment).split(", "):
        if part == "nothing":
            if output.strip():
                return f"wanted nothing, got {lines[0]!r}"
        elif m := re.fullmatch(r"exit (\d+)", part):
            if code != int(m.group(1)):
                return f"wanted {part}, got exit {code}"
        elif not any(l == part or l.startswith(part + " ") for l in lines):
            return f"wanted a line {part!r}, got {(lines[-1] if lines else 'nothing')!r}"
    return None


def run_verify(line, worktree, base, env):
    m = COMMENT.match(line)
    command, comment = (m.group(1), m.group(2)) if m else (line, None)
    command = re.sub(r"\bmain\b", base, command)
    run = subprocess.run([bash(), "-c", command], cwd=worktree, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env)
    if comment is None:
        return None if run.returncode == 0 else f"exit {run.returncode}"
    return expected(comment, run.returncode, run.stdout + run.stderr)


def joined(lines):
    """The lines, a line indented less than a `broken:` line before it joined to it: a report
    recorded across lines."""
    indent = lambda line: len(line) - len(line.lstrip())
    out = []
    for line in lines:
        if out and BROKEN.match(out[-1]) and line.strip() and indent(line) < indent(out[-1]):
            out[-1] += "\n" + line
        else:
            out.append(line)
    return out


def normal(report):
    """A report as compared: temporary names aside, and a newline and a run of backslashes read as
    the escapes they were pasted from."""
    report = TEMP_NAME.sub("tmp*", PR_SUFFIX.sub("", report.strip()))
    return re.sub(r"\\+", r"\\", report.replace("\n", "\\n"))


def run_break(entry, worktree, env):
    """What break.py reported for the recorded break, or why it did not."""
    command = entry["command"]
    if command[0] == "bash":
        command = [bash(), *command[1:]]
    run = subprocess.run([sys.executable, BREAK, "--file", os.path.join(worktree, entry["file"]),
                          "--find", entry["find"], "--replace", entry["replace"], "--what", entry["what"],
                          "--cwd", worktree, "--", *command],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    lines = (run.stdout + run.stderr).strip().splitlines()
    if run.returncode != 0:
        return None, lines[0] if lines else f"break.py exited {run.returncode}"
    return lines[-1][len(f"broken: {entry['what']} → "):], None


def check_spec(path, ref):
    """[(ok, text)] for one spec."""
    name = os.path.basename(path)
    day = re.match(r"day-(\d{2})-", name)
    if not day:
        return [(False, f"{name}: not a day spec")]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    commit = close_commit(day.group(1), ref)
    if not commit:
        return [(False, f"{name}: no merged day-{day.group(1)}/close-the-day on {ref}")]
    results = [(True, f"{name}: close merged in {commit[:7]}")]
    ticked = criteria(text)

    for cid, lines in ticked.items():
        for cls, test in dict.fromkeys(TEST.findall("\n".join(lines))):
            ok = test_exists(commit, cls, test)
            results.append((ok, f"{cid} {cls}.{test} {'is' if ok else 'is not'} defined at {commit[:7]}"))

    breaks_file = os.path.join(os.path.dirname(path), "breaks", f"day-{day.group(1)}.json")
    recorded = {}
    if os.path.exists(breaks_file):
        with open(breaks_file, encoding="utf-8") as f:
            recorded = {e["what"]: e for e in json.load(f)}

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    worktree = tempfile.mkdtemp(prefix="evidence-")
    git("worktree", "add", "--detach", worktree, commit)
    try:
        base = git("rev-parse", f"{commit}^1").strip()
        for line in verify_lines(text):
            why = run_verify(line, worktree, base, env)
            results.append((why is None, f"Verify: {line.strip()}" + (f" → {why}" if why else "")))
        for cid, lines in ticked.items():
            for what, report in (m.groups() for l in joined(lines) if (m := BROKEN.match(l))):
                if what == "none":
                    continue
                if what not in recorded:
                    results.append((False, f"{cid} broken: {what} → no arguments in {breaks_file}"))
                    continue
                got, why = run_break(recorded[what], worktree, env)
                if why is None and normal(got) != normal(report):
                    why = f"reported {got!r}, the spec says {PR_SUFFIX.sub('', report)!r}"
                results.append((why is None, f"{cid} broken: {what}" + (f" → {why}" if why else "")))
    finally:
        git("worktree", "remove", "--force", worktree, check=False)
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("specs", nargs="+")
    p.add_argument("--ref", default="main")
    a = p.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    failed = 0
    for spec in a.specs:
        for ok, text in check_spec(spec, a.ref):
            print(f"{'ok  ' if ok else 'FAIL'}  {text}")
            failed += not ok
    print(f"{failed} failed" if failed else "all evidence holds")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
