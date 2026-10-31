"""List the ticked criteria that still describe the behaviour in force.

    python scripts/behaviour-index.py [--specs DIR] [--json PATH]

The criteria parser is shared with spec-drift.py so their reading of specs stays in step.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_DRIFT = importlib.util.spec_from_file_location("spec_drift", os.path.join(HERE, "spec-drift.py"))
sd = importlib.util.module_from_spec(SPEC_DRIFT)
SPEC_DRIFT.loader.exec_module(sd)
DAY_FILE = re.compile(r"day-(\d+)-[^/\\]+\.md$")
REPLACES = re.compile(r"^[ \t]*Replaces:(.*)$", re.M)
WAS = re.compile(r"\s\u2014\s*was:\s*\S")


def collect(specs_dir):
    """Read day specs in numeric order, preserving the parser's criterion claims and tests."""
    rows = []
    problems = {"unknown": [], "order": [], "duplicate": [], "malformed": [], "missing_id": []}
    days = sorted((int(m.group(1)), name) for name in os.listdir(specs_dir)
                  if (m := DAY_FILE.fullmatch(name)))
    for day, filename in days:
        path = os.path.join(specs_dir, filename)
        with open(path, encoding="utf-8-sig", newline=None) as f:
            text = f.read()
        # One block per criterion, split as criteria() splits, and parsed on its own, so a
        # Replaces: line always belongs to the criterion whose block holds it.
        for block in re.split(r"^(?=- \[[ x]\])", sd.section(text, "Acceptance criteria"), flags=re.M):
            parsed = sd.criteria(block) if re.match(r"- \[[ x]\]", block) else []
            if not parsed:
                continue
            crit = parsed[0]
            row = {"day": day, "id": crit["id"], "tag": crit["kind"] or "untagged",
                   "claim": crit["claim"], "tests": crit["tests"], "spec": filename,
                   "ticked": crit["ticked"], "replaces": []}
            if not crit["id"]:
                problems["missing_id"].append(f"{filename}: {crit['claim']}")
            for line in REPLACES.findall(block):
                ids = re.findall(r"\bC\d+\.\d+\b", line.split("\u2014")[0])
                if not ids or not WAS.search(line):
                    problems["malformed"].append(f"{filename} {crit['id'] or ''}: Replaces:{line}")
                row["replaces"].extend(ids)
            rows.append(row)

    by_id = {}
    for row in rows:
        if row["id"]:
            by_id.setdefault(row["id"], []).append(row)
    replaced = set()
    for row in rows:
        if not row["ticked"]:
            continue
        for target in row["replaces"]:
            prior = by_id.get(target, [])
            if not prior:
                problems["unknown"].append(f"{row['spec']} {row['id']}: {target}")
                continue
            if not any(old["day"] < row["day"] for old in prior):
                problems["order"].append(f"{row['spec']} {row['id']}: {target}")
                continue
            if target in replaced:
                problems["duplicate"].append(f"{row['spec']} {row['id']}: {target}")
            else:
                replaced.add(target)

    for row in rows:
        row["state"] = ("unticked" if not row["ticked"] else
                        "replaced" if row["id"] in replaced else "in force")
    return rows, problems


def markdown(rows, problems):
    active_rows = [r for r in rows if r["state"] == "in force"]
    active = sum(r["state"] == "in force" for r in rows)
    retired = sum(r["state"] == "replaced" for r in rows)
    open_ = sum(r["state"] == "unticked" for r in rows)
    lines = [f"{active} criteria in force, {retired} replaced, {open_} unticked", "",
             "| Day | ID | Tag | Claim | Tests | Spec file |", "|---:|---|---|---|---|---|"]
    for r in active_rows:
        cells = [f"{r['day']:02d}", r["id"] or "", r["tag"], r["claim"], ", ".join(r["tests"]), r["spec"]]
        lines.append("| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    labels = {"unknown": "Unknown replacement IDs", "order": "Replacement is not from an earlier day",
              "duplicate": "Criteria replaced more than once",
              "malformed": "Replaces: lines without an ID or — was:", "missing_id": "Criteria without IDs"}
    for key, title in labels.items():
        if problems[key]:
            lines.extend(["", f"## {title}", "", *[f"- {p}" for p in problems[key]]])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--specs", default="specs", help="directory containing day specs")
    parser.add_argument("--json", metavar="PATH", help="also write the rows as JSON")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows, problems = collect(args.specs)
    print(markdown(rows, problems), end="")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump([{k: r[k] for k in ("day", "id", "tag", "claim", "tests", "spec", "state")}
                       for r in rows if r["state"] == "in force"],
                      f, indent=2, ensure_ascii=False)
            f.write("\n")
    if any(problems.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
