"""Score E1: each answerer's records against the set's labels, by the plan's rules.

    python experiments/jev/score.py --set <dir>/set.json [--results <dir>]

Per label kind, never pooled (docs/workflow-improvement-plan.md, "Scoring, fixed before the
first call"): flags on the hand-written insufficient and contradicts cases, false alarms on real
supports cases, both again on compound cases, exact agreement with the label, Brier score and a
ten-bin reliability table of the stated probability against "the answer is the label", and cost
and seconds per bundle where the records hold them. Then the four bars. Prints Markdown.
"""
import argparse
import json
import os

from run import RESULTS, load_set, recorded

ANSWERERS = ("jev", "opus", "floor")
HARD = ("insufficient", "contradicts")


def flagged(r):
    return r["recommendation"] == "flag"


def score(cases, recs):
    """{name: count or figure} for one answerer; errors are neither flags nor passes (rule 6)."""
    every = {c["id"]: c for c in cases if c["id"] in recs and not recs[c["id"]]["error"]}
    ok = {i: c for i, c in every.items() if not c.get("ambiguous")}
    hard = [c for c in ok.values() if c["kind"] in HARD]
    supports = [c for c in ok.values() if c["kind"] == "real" and c["label"] == "supports"]
    amb = [c for c in every.values() if c.get("ambiguous")]
    s = {"answered": len(ok), "errors": sum(1 for c in cases if recs.get(c["id"], {}).get("error")),
         "abstained": sum(recs[i]["abstained"] for i in ok),
         "hard": len(hard), "hard_flagged": sum(flagged(recs[c["id"]]) for c in hard),
         "supports": len(supports), "false_alarms": sum(flagged(recs[c["id"]]) for c in supports),
         "ambiguous": " ".join(f"{c['id']} ({c['label']}): {recs[c['id']]['answer']} "
                               f"{recs[c['id']]['probability']}" for c in amb) or "none"}
    real_ins = [c for c in ok.values() if c["kind"] == "real" and c["label"] == "insufficient"]
    s["real_insufficient"] = len(real_ins)
    s["real_insufficient_flagged"] = sum(flagged(recs[c["id"]]) for c in real_ins)
    for kind in ("real", "swapped", "insufficient", "contradicts"):
        of = [c for c in ok.values() if c["kind"] == kind]
        s[f"{kind}_n"], s[f"{kind}_exact"] = len(of), sum(recs[c["id"]]["answer"] == c["label"] for c in of)
        s[f"{kind}_flagged"] = sum(flagged(recs[c["id"]]) for c in of)
    comp = [c for c in ok.values() if c.get("compound")]
    s["compound_hard"] = sum(c["kind"] in HARD for c in comp)
    s["compound_hard_flagged"] = sum(flagged(recs[c["id"]]) for c in comp if c["kind"] in HARD)
    s["compound_supports"] = sum(c["kind"] == "real" and c["label"] == "supports" for c in comp)
    s["compound_false_alarms"] = sum(flagged(recs[c["id"]]) for c in comp
                                     if c["kind"] == "real" and c["label"] == "supports")
    pairs = [(recs[i]["probability"], recs[i]["answer"] == ok[i]["label"]) for i in ok
             if recs[i]["probability"] is not None]
    s["brier"] = sum((p - hit) ** 2 for p, hit in pairs) / len(pairs) if pairs else None
    s["bins"] = [[(p, hit) for p, hit in pairs if min(int(p * 10), 9) == b] for b in range(10)]
    costs = [recs[i]["cost_usd"] for i in ok if recs[i]["cost_usd"] is not None]
    secs = [recs[i]["seconds"] for i in ok if recs[i]["seconds"] is not None]
    s["cost_per_bundle"] = sum(costs) / len(costs) if costs else None
    s["seconds_per_bundle"] = sum(secs) / len(secs) if secs else None
    return s


def report(cases, scores):
    rows = [("answered (errors, abstained)", lambda s: f"{s['answered']} ({s['errors']}, {s['abstained']})"),
            ("hand-written insufficient + contradicts flagged", lambda s: f"{s['hard_flagged']} of {s['hard']}"),
            ("real supports flagged (false alarms)", lambda s: f"{s['false_alarms']} of {s['supports']}"),
            ("real insufficient flagged", lambda s: f"{s['real_insufficient_flagged']} of {s['real_insufficient']}"),
            ("compound: hard flagged", lambda s: f"{s['compound_hard_flagged']} of {s['compound_hard']}"),
            ("compound: false alarms", lambda s: f"{s['compound_false_alarms']} of {s['compound_supports']}")]
    for kind in ("real", "swapped", "insufficient", "contradicts"):
        rows.append((f"{kind}: answer is the label", lambda s, k=kind: f"{s[k + '_exact']} of {s[k + '_n']}"))
    rows += [("ambiguous, scored apart (label): answer", lambda s: s["ambiguous"]),
             ("Brier score", lambda s: "n/a" if s["brier"] is None else f"{s['brier']:.3f}"),
             ("cost per bundle, USD", lambda s: "not recorded" if s["cost_per_bundle"] is None
              else f"{s['cost_per_bundle']:.7f}"),
             ("seconds per bundle", lambda s: "not recorded" if s["seconds_per_bundle"] is None
              else f"{s['seconds_per_bundle']:.2f}")]
    names = [n for n in ANSWERERS if n in scores]
    out = ["| | " + " | ".join(names) + " |", "|---" * (len(names) + 1) + "|"]
    out += [f"| {label} | " + " | ".join(f(scores[n]) for n in names) + " |" for label, f in rows]
    out += ["", "Reliability, stated probability against \"the answer is the label\" (right of n):", "",
            "| bin | " + " | ".join(names) + " |", "|---" * (len(names) + 1) + "|"]
    for b in range(10):
        cells = []
        for n in names:
            got = scores[n]["bins"][b]
            cells.append(f"{sum(h for _, h in got)} of {len(got)}" if got else "")
        if any(cells):
            out.append(f"| {b / 10:.1f}-{(b + 1) / 10:.1f} | " + " | ".join(cells) + " |")
    if "jev" in scores and "opus" in scores:
        j, o = scores["jev"], scores["opus"]
        bars = [("1. useful on its own: flags at least half the hand-written cases", 2 * j["hard_flagged"] >= j["hard"]),
                ("2. not noisy: at most 1 in 10 real supports flagged", 10 * j["false_alarms"] <= j["supports"]),
                ("3. at least as good as the Opus agent: as many flags, no more false alarms",
                 j["hard_flagged"] >= o["hard_flagged"] and j["false_alarms"] <= o["false_alarms"]),
                ("4. cheaper per bundle than the Opus agent", None if o["cost_per_bundle"] is None
                 else j["cost_per_bundle"] < o["cost_per_bundle"])]
        out += ["", "The bar, for Jev:", ""]
        out += [f"- {text}: " + ({True: "met", False: "**not met**", None: "see the results"}[met])
                for text, met in bars]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--set", required=True)
    p.add_argument("--results", default=RESULTS)
    args = p.parse_args(argv)
    cases, _ = load_set(args.set)
    scores = {}
    for name in ANSWERERS:
        path = os.path.join(args.results, f"{name}.jsonl")
        if os.path.exists(path):
            scores[name] = score(cases, recorded(path))
    print(report(cases, scores))


if __name__ == "__main__":
    main()
