"""Build E1's set: one bundle per case, from Days 1-5's specs and breaks, each pinned to its close.

    python experiments/jev/e1/build.py --out <dir> [--ref main]

Writes <dir>/set.json and prints the count of each kind and the set's sha256, which
experiments/jev/e1/set.sha256 freezes. Reads only what is committed: specs/day-*.md,
specs/breaks/day-NN.json and cases.json beside this file. No model is called.

A criterion is used only if every check scripts/evidence.py runs on it passes, so no answerer is
credited for catching a malformed record. Its check is its source at the merge commit of its day's
close: each test the criterion names or a `broken:` line runs, with its file's module-level
helpers, and each break command that is not a test. `real`, `insufficient` and `contradicts`
cases come from cases.json, labelled by hand (rubric.md). `swapped` cases are built here: each
`broken:` line of a used criterion is paired with a criterion of another day that it cannot touch.
A break in the CLI's code or in tests/test_cli.py goes to a criterion whose check is the frozen
word rule; a break in the word rule or its tests goes to a criterion checked through the CLI.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import evidence  # noqa: E402

LABELS = {"supports", "insufficient", "contradicts", "unrelated"}
WORD_RULE = ("tests/contract/", "wordtally/count.py")
# The CLI criteria whose test input a change to how words split can change: "éé", which WORD does
# not match, and "dog,". Read from tests/test_cli.py's inputs; the rest are lowercase words and spaces.
SPLIT_SENSITIVE = {"C2.3", "C4.1", "C5.1"}


def criterion_text(lines):
    """The criterion as a reader sees it, up to its evidence, the tick dropped."""
    out = []
    for line in lines:
        if line.strip().startswith(("Evidence:", "broken:")):
            break
        out.append(line.strip())
    return re.sub(r"^- \[x\] ", "", "\n".join(out))


def breaks_and_notes(lines):
    """[(what, report)] of the `broken:` lines, and the notes in parentheses recorded among them."""
    found, notes, note = [], [], None
    for line in evidence.joined(lines):
        m = evidence.BROKEN.match(line)
        if m:
            found.append((m.group(1), evidence.PR_SUFFIX.sub("", m.group(2).strip())))
        elif found and (note is not None or line.strip().startswith("(")):
            note = (note + " " if note else "") + line.strip()
            if note.endswith(")"):
                notes.append(note)
                note = None
    return found, notes


def method(source, cls, name):
    """The method's source in the class, or None."""
    block = re.search(rf"^class {cls}\b.*?(?=^\S|\Z)", source, re.M | re.S)
    m = block and re.search(rf"^    def {name}\(.*?(?=^    \S|^\S|\Z)", block.group(0), re.M | re.S)
    return m.group(0).rstrip() if m else None


def check(commit, tests, commands):
    """The check's source: each file's helpers once, then each test, then each other command."""
    parts, preambles = [], {}
    for cls, name in tests:
        for hit in evidence.git("grep", "-l", "-E", rf"^class {cls}\b", commit, "--", "tests").split():
            source = evidence.git("show", hit)
            body = method(source, cls, name)
            if body:
                path = hit.split(":", 1)[1]
                if path not in preambles:
                    preambles[path] = source[:source.index(f"class {cls}")].rstrip()
                    parts.append(f"# {path}\n{preambles[path]}")
                parts.append(f"# {path}, {cls}\n{body}")
                break
        else:
            raise SystemExit(f"{cls}.{name} not found at {commit[:7]}")
    return parts + [f"$ {c}" for c in commands]


def criteria(ref):
    """{cid: criterion} for each ticked criterion of Days 1-5 that scripts/evidence.py passes."""
    found = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "specs", "day-0[1-5]-*.md"))):
        day = re.match(r"day-(\d{2})-", os.path.basename(path)).group(1)
        failed = {r.split(" ", 1)[0] for ok, r in evidence.check_spec(path, ref) if not ok}
        if failed - {cid for cid in failed if re.fullmatch(r"C\d+\.\d+", cid)}:
            raise SystemExit(f"day {day}: a check outside a criterion failed: {sorted(failed)}")
        with open(path, encoding="utf-8") as f:
            ticked = evidence.criteria(f.read())
        with open(os.path.join(ROOT, "specs", "breaks", f"day-{day}.json"), encoding="utf-8") as f:
            recorded = {e["what"]: e for e in json.load(f)}
        commit = evidence.close_commit(day, ref)
        for cid, lines in ticked.items():
            if cid in failed:
                print(f"left out: {cid}, scripts/evidence.py fails it")
                continue
            broken, notes = breaks_and_notes(lines)
            entries = [recorded[what] for what, _ in broken]
            tests = list(dict.fromkeys(evidence.TEST.findall("\n".join(lines))))
            commands = []
            for e in entries:
                cmd = e["command"]
                if cmd[:3] == ["python", "-m", "unittest"] and cmd[3].count(".") >= 3:
                    tests.append(tuple(cmd[3].split(".")[-2:]))
                else:
                    commands.append(shlex.join(cmd))
            found[cid] = {"day": day, "commit": commit, "text": criterion_text(lines),
                          "breaks": broken, "notes": notes, "files": [e["file"] for e in entries],
                          "check": check(commit, list(dict.fromkeys(tests)), list(dict.fromkeys(commands)))}
    return found


def kind(files):
    """What a criterion's breaks show it is checked through: the word rule, the CLI, or the suite."""
    if any(f.startswith("tests/contract/") for f in files):
        return "word rule"
    if all(f.startswith("wordtally/") and not f.startswith(WORD_RULE) for f in files):
        return "cli"
    return "suite"


def swaps(found):
    """[(from cid, break index, to cid)]: every break, each to a criterion of another day it cannot touch."""
    out = []
    for cid, c in found.items():
        for i, file in enumerate(c["files"]):
            to = "cli" if file.startswith(WORD_RULE) else "word rule"
            targets = [t for t, o in found.items() if o["day"] != c["day"] and o["files"] and kind(o["files"]) == to
                       and not (file == "wordtally/count.py" and t in SPLIT_SENSITIVE)]
            out.append((cid, i, targets[len(out) % len(targets)]))
    return out


def bundle(c, breaks, notes):
    return {"criterion": c["text"], "check": c["check"],
            "breaks": [f"broken: {what} → {report}" for what, report in breaks], "notes": notes}


def build(found, cases):
    real = {cid for cid, c in found.items() if c["breaks"]}
    labelled = [c["criterion"] for c in cases if c["kind"] == "real"]
    if sorted(labelled) != sorted(real):
        raise SystemExit(f"cases.json labels {sorted(labelled)}, the set has {sorted(real)}")
    out = []
    for case in cases:
        if case["label"] not in LABELS or case["criterion"] not in real:
            raise SystemExit(f"{case['id']}: label {case['label']!r} or criterion {case['criterion']!r}")
        c = found[case["criterion"]]
        keep = case.get("breaks", range(len(c["breaks"])))
        reports = case.get("reports", {})
        broken = [(c["breaks"][i][0], reports.get(str(i), c["breaks"][i][1])) for i in keep]
        out.append({**case, "day": c["day"], "commit": c["commit"], "bundle": bundle(c, broken, c["notes"])})
    for n, (src, i, dst) in enumerate(swaps(found), 1):
        c = found[dst]
        out.append({"id": f"S{n:02d}", "kind": "swapped", "criterion": dst, "from": f"{src} break {i}",
                    "label": "unrelated", "reason": f"a Day {found[src]['day']} break on a Day {c['day']} criterion",
                    "by": "build.py", "day": c["day"], "commit": c["commit"],
                    "bundle": bundle(c, [found[src]["breaks"][i]], [])})
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out", required=True)
    p.add_argument("--ref", default="main")
    args = p.parse_args(argv)
    with open(os.path.join(HERE, "cases.json"), encoding="utf-8") as f:
        cases = json.load(f)
    os.chdir(ROOT)
    # C4.2's break makes --stopwords take the file's name, and wordtally then reads standard input:
    # the checks inherit it, so a terminal's would wait for ever.
    os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
    out = build(criteria(args.ref), cases)
    data = json.dumps(out, ensure_ascii=False, sort_keys=True, indent=1).encode("utf-8")
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "set.json"), "wb") as f:
        f.write(data)
    for kind in ("real", "swapped", "insufficient", "contradicts"):
        print(f"{kind}: {sum(c['kind'] == kind for c in out)}")
    print(f"sha256: {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
