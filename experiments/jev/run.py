"""Run E1: ask an answerer the rubric's question about each bundle, and record every call.

    python experiments/jev/run.py ask --set <dir>/set.json --answerer jev|floor [--only R01,S02] [--dry-run]
    python experiments/jev/run.py prompts --set <dir>/set.json --to <dir>
    python experiments/jev/run.py ingest --set <dir>/set.json --answers <file>

`ask` sends each bundle to Jev through OpenRouter's Decisions API, or answers `supports` for the
floor, and appends one record per call to experiments/jev/e1/results/<answerer>.jsonl. A case
already recorded is skipped, unless its record is an error and --retry-errors is given. `prompts`
writes one file per case for the Opus agent, the same question and bundle in words; `ingest` turns
the agent's answers, {case: {"answer", "probability"} or {"abstain": true}}, into opus.jsonl.

The set must be the one experiments/jev/e1/set.sha256 froze: build it with e1/build.py. The
question and the labels are read from e1/rubric.md, so every answerer gets the same words. The key
is OPENROUTER_API_KEY and the model JEV_MODEL, from the environment or the repository's .env; the
key is never printed or recorded.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
E1 = os.path.join(HERE, "e1")
RESULTS = os.path.join(E1, "results")
URL = "https://openrouter.ai/api/alpha/decisions"
THRESHOLD = 0.9  # docs/workflow-improvement-plan.md, "Scoring, fixed before the first call"


def rubric(path=os.path.join(E1, "rubric.md")):
    """(question, {label: when}) as rubric.md states them, version 1."""
    with open(path, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    section = lambda title: text.split(f"\n## {title}\n", 1)[1].split("\n## ", 1)[0]  # noqa: E731
    question = " ".join(line[2:] for line in section("The question, version 1").splitlines()
                        if line.startswith("> "))
    labels = dict(re.findall(r"^\| `(\w+)` \| (.+?) \|$", section("The labels"), re.M))
    return question, labels


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")


def load_set(path):
    """The set's cases and digest, refused unless the digest is the one set.sha256 froze."""
    with open(path, "rb") as f:
        data = f.read()
    with open(os.path.join(E1, "set.sha256"), encoding="utf-8") as f:
        frozen = f.read().split()[0]
    if sha256(data) != frozen:
        raise SystemExit(f"{path}: sha256 {sha256(data)}, set.sha256 froze {frozen}")
    return json.loads(data), frozen


def questions():
    question, labels = rubric()
    return {"verdict": {"type": "choice", "instructions": question, "criteria": labels}}


def recommendation(answer, probability):
    """flag or pass, by the plan's rule: any answer but supports, or supports below 0.9, is a flag.
    An abstention (no answer) is a flag; an error gives none, and is not called here."""
    if answer != "supports" or probability is None or probability < THRESHOLD:
        return "flag"
    return "pass"


def secrets():
    """(key, model) from the environment, then from .env at the repository's root."""
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip("'\"")
    get = lambda name: os.environ.get(name) or env.get(name, "")  # noqa: E731
    return get("OPENROUTER_API_KEY"), get("JEV_MODEL")


def post(key, body, timeout=120):
    """(HTTP status, response text), never raising on an HTTP or network error."""
    req = urllib.request.Request(URL, data=canonical(body), method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"


def parse_jev(status, text):
    """{answer, probability, probabilities, confidence, served, cost_usd} or {error}."""
    if status != 200:
        return {"error": f"HTTP {status}: {text[:500]}"}
    try:
        data = json.loads(text)
        a = data["answers"]["verdict"]
        answer, probs = a["choice"], a["probabilities"]
        if a.get("type") != "choice" or answer not in probs:
            raise ValueError(f"answer {answer!r} not among {sorted(probs)}")
        return {"answer": answer, "probability": probs[answer], "probabilities": probs,
                "confidence": a.get("confidence"), "served": data.get("model"),
                "cost_usd": (data.get("usage") or {}).get("cost")}
    except (ValueError, KeyError, TypeError) as e:
        return {"error": f"malformed: {type(e).__name__}: {e}: {text[:500]}"}


def record(case, answerer, set_sha, question_version, model, result, seconds):
    error = result.get("error")
    return {"case": case["id"], "answerer": answerer, "commit": case["commit"], "set_sha256": set_sha,
            "bundle_sha256": sha256(canonical(case["bundle"])), "question": question_version,
            "model": model, "served": result.get("served"), "answer": result.get("answer"),
            "probability": result.get("probability"), "probabilities": result.get("probabilities"),
            "confidence": result.get("confidence"), "abstained": bool(result.get("abstained")),
            "recommendation": None if error else recommendation(result.get("answer"), result.get("probability")),
            "cost_usd": result.get("cost_usd"), "seconds": seconds, "error": error,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "runner": head()}


def head():
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or None


def recorded(path):
    """{case: last record} of a results file."""
    done = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done[r["case"]] = r
    return done


def append(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as f:
        f.write(canonical(rec) + b"\n")


def ask(cases, set_sha, answerer, out, only=None, retry_errors=False, dry_run=False, send=post):
    qs = questions()
    version = "v1:" + sha256(canonical(qs))[:12]
    key, model = secrets() if answerer == "jev" else ("", "floor")
    if answerer == "jev" and not dry_run and not (key and model):
        raise SystemExit("OPENROUTER_API_KEY and JEV_MODEL must be set, in the environment or .env")
    path = os.path.join(out, f"{answerer}.jsonl")
    done = recorded(path)
    counts = {"asked": 0, "skipped": 0, "errors": 0}
    for case in cases:
        prior = done.get(case["id"])
        if (only and case["id"] not in only) or (prior and not (retry_errors and prior["error"])):
            counts["skipped"] += 1
            continue
        body = {"model": model, "state": case["bundle"], "questions": qs}
        if dry_run:
            print(f"{case['id']}: would send {len(canonical(body))} bytes to {model or '(no JEV_MODEL)'}")
            continue
        start = time.monotonic()
        if answerer == "floor":
            result = {"answer": "supports", "probability": 1.0, "served": "floor"}
        else:
            result = parse_jev(*send(key, body))
        rec = record(case, answerer, set_sha, version, model, result, round(time.monotonic() - start, 3))
        append(path, rec)
        counts["asked"] += 1
        counts["errors"] += bool(rec["error"])
        print(f"{case['id']}: " + (rec["error"] or f"{rec['answer']} {rec['probability']}"))
    print(f"asked: {counts['asked']}, errors: {counts['errors']}, skipped: {counts['skipped']}, file: {path}")
    return counts


def prompt(case):
    question, labels = rubric()
    table = "\n".join(f"- `{label}`: {when}" for label, when in labels.items())
    return (f"{question}\n\nThe labels:\n{table}\n\nThe bundle, as JSON:\n\n"
            f"```json\n{json.dumps(case['bundle'], ensure_ascii=False, indent=1)}\n```\n\n"
            'Reply with JSON only: {"answer": "<label>", "probability": <0 to 1>}, or, if you cannot '
            'answer, {"abstain": true, "reason": "<one line>"}.\n')


def prompts(cases, to):
    os.makedirs(to, exist_ok=True)
    for case in cases:
        with open(os.path.join(to, f"{case['id']}.md"), "wb") as f:
            f.write(prompt(case).encode("utf-8"))
    print(f"{len(cases)} prompts in {to}")


def ingest(cases, set_sha, answers, out):
    version = "v1:" + sha256(canonical(questions()))[:12]
    _, labels = rubric()
    path = os.path.join(out, "opus.jsonl")
    for case in cases:
        a = answers.get(case["id"])
        if a is None:
            continue
        if a.get("abstain"):
            result = {"abstained": True}
        elif a.get("answer") in labels and isinstance(a.get("probability"), (int, float)):
            result = {"answer": a["answer"], "probability": a["probability"]}
        else:
            result = {"error": f"malformed: {json.dumps(a)[:500]}"}
        result.update(served=a.get("served"), cost_usd=a.get("cost_usd"))
        append(path, record(case, "opus", set_sha, version, a.get("model"), result, a.get("seconds")))
    print(f"{sum(c['id'] in answers for c in cases)} answers into {path}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask")
    a.add_argument("--set", required=True)
    a.add_argument("--answerer", choices=["jev", "floor"], required=True)
    a.add_argument("--only", help="comma-separated case ids")
    a.add_argument("--retry-errors", action="store_true")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--out", default=RESULTS)
    pr = sub.add_parser("prompts")
    pr.add_argument("--set", required=True)
    pr.add_argument("--to", required=True)
    i = sub.add_parser("ingest")
    i.add_argument("--set", required=True)
    i.add_argument("--answers", required=True)
    i.add_argument("--out", default=RESULTS)
    args = p.parse_args(argv)
    cases, set_sha = load_set(args.set)
    if args.cmd == "ask":
        only = set(args.only.split(",")) if args.only else None
        ask(cases, set_sha, args.answerer, args.out, only, args.retry_errors, args.dry_run)
    elif args.cmd == "prompts":
        prompts(cases, args.to)
    else:
        with open(args.answers, encoding="utf-8") as f:
            ingest(cases, set_sha, json.load(f), args.out)


if __name__ == "__main__":
    main()
