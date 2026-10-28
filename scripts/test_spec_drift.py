"""The dashboard's numbers move when they should and only then.

Each drift test builds a small git repository, one commit per merge, and runs spec-drift.py's
trajectory over it; the roadmap tests check the run order, the statuses and the next step. Needs
git and numpy; the page tests run docs/dashboard/dashboard.js and need node.

    python scripts/test_spec_drift.py
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("spec_drift", os.path.join(HERE, "spec-drift.py"))
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)
COMPARE = os.path.join(HERE, "..", "kit", "compare-page.py")

PLAN = "# Plan\n\nThe plan names `FooService` and `bar_table`.\n"
DAY = "# Day 01\n\nThe day adds `FooService`, then the rest of the day.\n"
# The source project's file under neutral names: its two tests renamed to another stem,
# its six directory moves, its Verify base, its four services by package, and its infra workflow.
PROJECT = dict(
    renamed=[[296, "OrdersUserDeletedConsumerIT", "UserDeletedConsumerTest"],
             [298, "CircuitBreakerIT", "StockLookupBreakerTest"]],
    moved=[[174, "core/stock", "services/stock-service"], [224, "core/pricing", "services/pricing-service"],
           [296, "core/orders", "services/order-service"], [315, "core", "services/account-service"],
           [416, "services/account-service/docs", "docs/system"],
           [419, "services/account-service/app", "services/account-service"]],
    verify_bases=["core"], package_root="org.example.shop",
    services=dict(auth="account", user="account", profile="account", account="account", stock="stock",
                  catalog="stock", saved="orders", orders="orders", pricing="pricing"),
    infra_workflow="infra.yaml")


def use_project(test, fields):
    """fields as the project file, read as spec-drift.py reads its own, until the test ends."""
    folder = tempfile.mkdtemp(prefix="spec-drift-config-")
    test.addCleanup(shutil.rmtree, folder, True)
    path = os.path.join(folder, "spec-drift.config.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fields, f)
    for name, value in sd.project_config(path).items():
        test.addCleanup(setattr, sd, name, getattr(sd, name))
        setattr(sd, name, value)


class Repo:
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="spec-drift-test-")
        self.git("init", "-q")
        self.snaps = []

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                               *args], cwd=self.path, capture_output=True, text=True, check=True).stdout

    def merge(self, files):
        """One commit, standing in for one merge on main."""
        for name, text in files.items():
            full = os.path.join(self.path, name)
            if text is None:  # deleted, or moved when the new path is in the same merge
                os.remove(full)
                continue
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"merge {len(self.snaps)}")
        n = len(self.snaps)
        self.snaps.append(dict(sha=self.git("rev-parse", "--short", "HEAD").strip(), date="2026-09-20",
                               pr=n or None, title=f"Day 01 track A: {n}", branch="day-01/track-a-x" if n else ""))
        return self

    def rows(self):
        return self.inside(lambda blobs: sd.trajectory([dict(s) for s in self.snaps], blobs)[0])

    def inside(self, fn):
        """fn(blobs), run in the repository."""
        cwd = os.getcwd()
        os.chdir(self.path)
        try:
            with sd.Blobs() as blobs:
                return fn(blobs)
        finally:
            os.chdir(cwd)

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


class SpecDriftTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo().merge({"plan.md": PLAN, "specs/day-01-x.md": DAY, "src/App.java": "class App {}\n"})

    def tearDown(self):
        self.repo.close()

    def test_code_that_names_a_spec_name_narrows_the_gap(self):
        rows = self.repo.merge({"src/Foo.java": "class FooService {}\n"}).rows()
        self.assertIsNone(rows[0]["gap_full"])  # no spec name in the code: no direction to compare
        self.assertLess(rows[1]["gap_full"], 90.0)

    def test_name_coverage_is_the_share_of_spec_names_the_code_has(self):
        rows = self.repo.merge({"src/Foo.java": "class FooService { FooService f; }\n"}).rows()
        self.assertEqual((rows[0]["name_coverage"], rows[1]["name_coverage"]), (0.0, 0.5))  # bar_table not yet
        rows = self.repo.merge({"src/Bar.java": "bar_table b;\n"}).rows()
        self.assertEqual(rows[2]["name_coverage"], 1.0)
        rows = self.repo.merge({"plan.md": "# Plan\n\nThe plan names nothing.\n"}).rows()
        self.assertEqual(rows[3]["name_coverage"], 1.0)  # bar_table, in the code only, is not asked for

    def test_jaccard_counts_a_name_the_specs_dropped_but_the_code_keeps(self):
        rows = self.repo.merge({"src/Foo.java": "class FooService { bar_table b; }\n"}).rows()
        self.assertEqual((rows[1]["name_coverage"], rows[1]["jaccard"]), (1.0, 1.0))
        rows = self.repo.merge({"plan.md": "# Plan\n\nThe plan names nothing.\n"}).rows()
        self.assertEqual((rows[2]["name_coverage"], rows[2]["jaccard"]), (1.0, 0.5))  # bar_table: code only
        self.assertEqual((rows[1]["names_kept"], rows[2]["names_kept"]), (0, 1))

    def test_a_failed_blob_read_names_the_commit_and_the_path(self):
        sha = self.repo.snaps[0]["sha"]

        def read_after_git_dies(blobs):
            self.assertEqual(blobs.read(sha, "no/such/file"), "")  # missing is not a failure
            blobs.proc.kill()
            blobs.proc.wait()
            return blobs.read(sha, "plan.md")
        with self.assertRaises(RuntimeError) as failed:
            self.repo.inside(read_after_git_dies)
        self.assertIn(f"plan.md at {sha}", str(failed.exception))

    def test_a_run_from_the_cache_reads_what_a_fresh_one_does(self):
        # Merge 1 is cached before any spec names BazClient; merge 2's spec does, which shifts
        # every name's place in the vocabulary.
        self.addCleanup(sd.CACHE.clear)
        self.repo.merge({"src/Baz.java": "class BazClient { FooService f; }\n"})
        sd.CACHE.clear()
        self.repo.rows()
        self.repo.merge({"specs/day-01-x.md": DAY + "It calls `BazClient`.\n", "src/Use.java": "BazClient b;\n"})
        calls, real = [], sd.run
        sd.run = lambda *a: calls.append(a) or real(*a)
        try:
            cached = self.repo.rows()
            sd.CACHE.clear()
            fresh_from = len(calls)
            fresh = self.repo.rows()
        finally:
            sd.run = real
        self.assertEqual(cached, fresh)
        self.assertLess(fresh_from, len(calls) - fresh_from)

    def test_a_comment_naming_a_spec_name_is_not_code(self):
        rows = self.repo.merge({"src/Foo.java": "// FooService comes later\n /* FooService */\n",
                                "src/V1.sql": "-- bar_table comes later\nSELECT 1; -- bar_table\n",
                                "run.sh": "# FooService\n"}).rows()
        self.assertIsNone(rows[1]["gap_full"])

    def test_a_later_spec_name_does_not_move_an_earlier_gap(self):
        self.repo.merge({"src/Foo.java": "class FooService { BazClient baz; }\n"})
        before = self.repo.rows()[1]["gap_full"]
        self.repo.merge({"specs/day-01-x.md": DAY + "It calls `BazClient`.\n"})
        self.assertEqual(self.repo.rows()[1]["gap_full"], before)

    def test_a_file_under_kit_is_tooling_and_not_code_the_gap_reads(self):
        self.repo.merge({"src/Foo.java": "class FooService {}\n"})
        rows = self.repo.merge({"kit/page/data.json": '{"names": "FooService bar_table bar_table bar_table"}\n'}).rows()
        self.assertEqual(rows[2]["gap_full"], rows[1]["gap_full"])
        self.assertEqual(rows[2]["work"], dict(spec=0, context=0, prod=0, test=0, tooling=1))

    def test_each_merge_counts_its_own_lines_by_box_and_a_move_only_what_changed(self):
        rows = self.repo.merge({"src/test/FooTest.java": "a\nb\n", "CLAUDE.md": "c\n", "specs/day-01-x.md": DAY + "d\n",
                                "scripts/x.py": "e\n", "package-lock.json": "{}\n", "src/Big.java": "f\ng\nh\ni\n"}).rows()
        self.assertEqual(rows[1]["work"], dict(spec=1, context=1, prod=4, test=2, tooling=1))
        os.remove(os.path.join(self.repo.path, "src", "Big.java"))
        rows = self.repo.merge({"src/test/BigTest.java": "f\ng\nh\ni\nj\n"}).rows()
        self.assertEqual(rows[2]["work"], dict(spec=0, context=0, prod=0, test=1, tooling=0))

    def test_a_file_goes_in_the_first_box_its_path_matches(self):
        for path, box in [("plan.md", "spec"), ("specs/README.md", "spec"), ("specs/day-01-test-harness.md", "spec"),
                          ("CLAUDE.md", "context"), ("backend/app/README.md", "context"), (".claude/agents/x.md", "context"),
                          (".claude/settings.json", "context"), ("docs/workflow.svg", "context"),
                          ("backend/app/src/test/java/x/support/Harness.java", "test"), ("services/job/src/FooIT.java", "test"),
                          ("scripts/test_spec_drift.py", "test"), ("data/tests/conftest.py", "test"), ("web/a.spec.ts", "test"),
                          ("scripts/spec-drift.py", "tooling"), (".github/workflows/ci.yml", "tooling"),
                          ("docs/dashboard/dashboard.js", "tooling"), ("backend/app/src/main/java/x/Latest.java", "prod"),
                          ("docker-compose.yml", "prod"), ("docs/dashboard/token-usage.json", None),
                          ("docs/dashboard/deployment.json", None),
                          ("frontend/package-lock.json", None), ("screenshots/a.png", None)]:
            self.assertEqual(sd.work_kind(path), box, path)
        self.assertEqual(sd.renamed_to("backend/{app => job}/src/X.java"), "backend/job/src/X.java")
        self.assertEqual(sd.renamed_to("src/{ => job}/X.java"), "src/job/X.java")
        self.assertEqual(sd.renamed_to("a.txt => b/a.txt"), "b/a.txt")

    def test_a_pr_records_a_break_in_one_fixed_line_and_nothing_else(self):
        checklist = "- [x] Spec changes only: each check has been seen to fail (see `specs/README.md`)\n"
        for body, state in [("broken: `ISSUER` back → `AuthIT` failed 2 of 8\n", "recorded"),
                            ("- broken: the guard removed -> expected: 401 but was: 200\n", "recorded"),
                            ("broken: none → this track adds no test\nbroken: the sort reversed → 3 red\n", "recorded"),
                            ("broken: none → this track adds no test\n", "none"),
                            # The free text the regexes read before #310 is not the line.
                            ("**Broken on purpose:** `ISSUER` back. It fails 2 of 8.\n", "silent"),
                            ("Seen red, broken: the guard removed → it failed\n", "silent"),
                            ("broken: the guard removed\n", "silent"),
                            ("", "silent"), (None, "silent")]:
            self.assertEqual(sd.break_state(body and body + checklist, 310), state, body)
        self.assertEqual(sd.break_state(checklist, 310), "silent")
        self.addCleanup(setattr, sd, "BREAK_LINE_FROM_PR", sd.BREAK_LINE_FROM_PR)
        sd.BREAK_LINE_FROM_PR = 310  # the source project asked for the line from #310
        self.assertEqual(sd.break_state("broken: the guard removed → 401\n", 309), "not measured")

    def test_a_new_project_reads_the_break_line_from_its_first_pr(self):
        self.assertEqual(sd.BREAK_LINE_FROM_PR, 0)
        self.assertEqual(sd.break_state("broken: the guard removed → 401\n", 1), "recorded")
        self.assertEqual(sd.break_state("No break.\n", 7), "silent")

    def test_ci_counts_each_pushed_commit_once_and_only_pull_request_runs(self):
        run = lambda sha, result, flow="PR checks", event="pull_request": dict(
            headBranch="day-01/track-a-x", headSha=sha, conclusion=result, workflowName=flow, event=event)
        runs = [run("a", "failure"), run("a", "failure", "Backend CI/CD"), run("a", "success", "Dashboard"),
                run("b", "success"), run("b", "cancelled", "Backend CI/CD"), run("c", "failure", event="push")]
        self.assertEqual(sd.ci_pushes(runs), {"day-01/track-a-x": (2, 1, ["Backend CI/CD", "PR checks"])})

    def test_a_gh_list_as_long_as_its_limit_is_refused(self):
        real = sd.run
        try:
            sd.run = lambda *args: "[" + ",".join(["{}"] * n) + "]"
            n = 2
            self.assertEqual(len(sd.gh_list(3, "pr", "list")), 2)
            n = 3
            with self.assertRaisesRegex(SystemExit, "pr list returned its limit of 3"):
                sd.gh_list(3, "pr", "list")
        finally:
            sd.run = real

    def test_a_gh_list_of_a_thousand_is_refused_under_a_larger_limit(self):
        # GitHub gives at most 1,000 for a filtered run list, so 1,000 may be cut whatever the limit.
        real = sd.run
        try:
            sd.run = lambda *args: "[" + ",".join(["{}"] * 1000) + "]"
            with self.assertRaisesRegex(SystemExit, "run list returned 1000"):
                sd.gh_list(5000, "run", "list")
            sd.run = lambda *args: "[" + ",".join(["{}"] * 999) + "]"
            self.assertEqual(len(sd.gh_list(5000, "run", "list")), 999)
        finally:
            sd.run = real

    def test_an_infra_run_whose_artifact_does_not_download_is_skipped(self):
        def fake(*args):
            if args[2] == "list":
                self.assertEqual(args[4], "infra.yaml")
                return json.dumps([dict(databaseId=2, headSha="b" * 40, conclusion="failure",
                                        createdAt="2026-10-08T10:00:00Z", url="u2"),
                                   dict(databaseId=1, headSha="a" * 40, conclusion="success",
                                        createdAt="2026-10-07T10:00:00Z", url="u1")])
            if args[3] == "2":
                raise subprocess.CalledProcessError(1, args)
            with open(os.path.join(args[-1], "infra-summary.json"), "w", encoding="utf-8") as f:
                json.dump({"criteria": {"C32.2": "pass"}}, f)
            return ""
        real = sd.run
        try:
            sd.run = fake
            got = sd.infra("infra.yaml")
        finally:
            sd.run = real
        self.assertEqual([r["sha"] for r in got["runs"]], ["bbbbbbb", "aaaaaaa"])
        self.assertEqual(got["latest"], dict(sha="aaaaaaa", conclusion="success", date="2026-10-07", url="u1",
                                             summary={"criteria": {"C32.2": "pass"}}))

    def test_with_no_github_remote_there_are_no_prs_and_a_note_says_so(self):
        def fake(*args):
            if args[1:3] == ("repo", "view"):
                if remote:
                    return "me"
                raise subprocess.CalledProcessError(1, args, stderr="no git remotes found")
            if args[1:3] == ("pr", "list"):
                return json.dumps([dict(number=1, author=dict(login="me")), dict(number=2, author=dict(login="x"))])
            return "[]"
        real = sd.run
        try:
            sd.run = fake
            remote = False
            self.assertEqual(sd.github(), ([], [], sd.NO_REMOTE))
            remote = True
            self.assertEqual(sd.github(), ([dict(number=1, author=dict(login="me"))], [], None))
        finally:
            sd.run = real
        self.assertTrue(sd.NO_REMOTE.startswith("No GitHub remote"))

    def test_the_deployment_is_its_checks_and_none_without_the_file(self):
        real = sd.PAGE
        sd.PAGE = tempfile.mkdtemp()
        try:
            self.assertIsNone(sd.deployment())
            checks = [dict(criterion="C35.16", name="the site answers", ok=True, detail="200", at="2026-10-10T09:00:00Z"),
                      dict(criterion="C35.17", name="login sets the cookie", ok=False, detail="no Secure",
                           at="2026-10-10T09:01:00Z")]
            with open(os.path.join(sd.PAGE, "deployment.json"), "w", encoding="utf-8") as f:
                json.dump(dict(domain="example.test", checkedAt="2026-10-10T09:01:00Z", checks=checks), f)
            self.assertEqual(sd.deployment()["checks"], checks)
        finally:
            shutil.rmtree(sd.PAGE)
            sd.PAGE = real

    def test_the_data_names_the_commit_versions_and_draws_that_made_it(self):
        p = sd.provenance()
        self.assertRegex(p["commit"], "^[0-9a-f]{40}$")
        self.assertEqual((p["numpy"], p["chance_draws"]), (sd.np.__version__, sd.CHANCE_DRAWS))
        self.assertRegex(p["python"], r"^3\.\d+\.\d+")
        self.assertIsInstance(p["script_edited"], bool)

    def test_a_day_that_runs_later_is_not_reached_by_a_higher_number(self):
        self.repo.merge({"specs/day-17-x.md": "Day 17 adds `LaterThing`.\n",
                         "specs/day-38-x.md": "Day 38 adds `PlatformThing`.\n"})
        self.repo.merge({"src/P.java": "class PlatformThing { FooService foo; }\n"})
        self.repo.snaps[-1]["branch"] = "day-38/track-a-x"
        by_number = self.repo.rows()[-1]["coverage"]
        rows, files = self.repo.inside(lambda blobs: sd.trajectory([dict(s) for s in self.repo.snaps], blobs,
                                                                   [1, 38, 17])[:2])
        self.assertEqual((by_number, rows[-1]["coverage"]), (0.667, 1.0))  # LaterThing is Day 17's
        self.assertEqual(files, ["plan.md", "specs/day-01-x.md", "specs/day-38-x.md", "specs/day-17-x.md"])
        self.repo.merge({"src/L.java": "class LaterThing {}\n"})
        self.repo.snaps[-1]["branch"] = "day-17/track-a-y"
        rows = self.repo.inside(lambda blobs: sd.trajectory([dict(s) for s in self.repo.snaps], blobs, [1, 38, 17])[0])
        self.assertEqual(rows[-1]["day"], 17)  # after 38 in the run order, though lower in number

    def test_a_wildcard_prefix_is_no_name_the_code_could_miss(self):
        self.assertFalse(sd.code_like("aws_ecs_"))
        self.assertFalse(sd.code_like("check_c34_"))
        self.assertTrue(sd.code_like("aws_ecs_service"))
        self.repo.merge({"src/Foo.java": "class FooService { FooService f; }\n"})
        rows = self.repo.merge({"specs/day-02-y.md": "It writes `aws_ecs_*`.\n", "src/Cloud.java": "aws_ecs_service e;\n"}).rows()
        self.assertEqual((rows[1]["name_coverage"], rows[2]["name_coverage"]), (0.5, 0.5))  # bar_table still missing

    def test_a_name_the_code_had_and_lost_is_retired_and_still_a_miss(self):
        self.repo.merge({"src/Foo.java": "class FooService { }\n"})
        rows = self.repo.merge({"src/Foo.java": None}).rows()
        self.assertEqual([r["names_retired"] for r in rows], [0, 0, 1])  # bar_table was never in the code
        self.assertEqual((rows[1]["name_coverage"], rows[2]["name_coverage"]), (0.5, 0.0))

    def test_code_in_the_spec_proportions_sits_below_chance(self):
        rows = self.repo.merge({"src/Foo.java": "class FooService { FooService f; bar_table b; }\n"}).rows()
        self.assertEqual((rows[0]["gap_full"], rows[0]["gap_chance"]), (None, None))  # no code: no angle
        self.assertEqual(rows[1]["gap_full"], 0.0)  # FooService twice and bar_table once, as the specs
        self.assertGreater(rows[1]["gap_chance"], 10.0)
        lo, hi = rows[1]["gap_chance_band"]
        self.assertTrue(lo <= rows[1]["gap_chance"] <= hi)
        rows = self.repo.merge({"src/Foo.java": "class FooService { bar_table a; bar_table b; }\n"}).rows()
        self.assertGreater(rows[2]["gap_full"], rows[1]["gap_full"])
        self.assertEqual(rows[2]["gap_chance"], rows[1]["gap_chance"])  # the same counts, shuffled

CRITERIA = """- [x] **hold** — Refused: `contract/FooIT` passes. Broken on purpose: the check removed.
      #2: `FooIT.refuses`.
      broken: the guard removed → `expected: 401 but was: 200`
- [x] **new** — Saved in `BarIT`, or a case added to `FooIT`. Red today: no table.
      #3: a case in `FooIT.saves`.
- [ ] **new** — Not started.
"""


class EvidenceTest(unittest.TestCase):
    """A closed day's evidence: what each criterion cites, and whether its tests are still there."""

    def setUp(self):
        # The day's PR is #1, the second commit; later commits stand for later days.
        self.repo = Repo().merge({"plan.md": PLAN}).merge(
            {"src/FooIT.java": "class FooIT { void refuses() {} void saves() {} }\n"})

    def tearDown(self):
        self.repo.close()

    def state(self):
        days = [dict(day=1, status="done", prs=[dict(number=1)], evidence=sd.criteria(CRITERIA))]
        return self.repo.inside(lambda blobs: sd.evidence(days, self.repo.snaps, blobs))[0]["evidence"]

    def test_a_criterion_is_read_for_its_kind_prs_tests_and_break(self):
        hold, new, open_ = sd.criteria(CRITERIA)
        self.assertEqual((hold["kind"], hold["ticked"], hold["prs"], hold["red"]), ("hold", True, [2], True))
        self.assertEqual(hold["tests"], ["FooIT", "FooIT.refuses"])
        self.assertEqual((new["red"], open_["ticked"], open_["prs"]), (False, False, []))
        self.assertTrue(hold["claim"].startswith("Refused: `contract/FooIT` passes."), hold["claim"])
        cut = sd.criteria("- [x] **hold** — " + "x" * 130 + " `a/LongNameIT`\n")[0]["claim"]
        self.assertEqual(cut.count("`"), 0)

    def test_a_criterion_from_day_28_on_carries_its_id_and_an_older_one_none(self):
        tagged, untagged = sd.criteria("- [ ] C28.3 **new** — `FooIT` refuses.\n- [ ] **hold** — C28.3 holds.\n")
        self.assertEqual((tagged["id"], tagged["kind"], tagged["claim"]), ("C28.3", "new", "`FooIT` refuses."))
        self.assertEqual((untagged["id"], untagged["claim"]), (None, "C28.3 holds."))

    def test_a_criterion_is_seen_red_only_by_a_broken_line_with_what_it_reported(self):
        red = lambda text: sd.criteria(f"- [x] C28.1 **hold** — X. #2: `FooIT`.\n      {text}\n")[0]["red"]
        self.assertTrue(red("broken: the guard removed → `FooIT` failed 1 of 3"))
        self.assertTrue(red("broken: the sort reversed -> 31 of 31 red"))
        # A baseline, a break planned but not reported, a `none`, or the free text the regexes read
        # before #310 is not a break seen red.
        for text in ["Red today: the route does not exist.", "broken: the guard removed",
                     "broken: none → the grep is the check",
                     "Broken on purpose in #74: the auth tests reported `Tests run: 49, Failures: 8`.",
                     "Red again with the migration's revoke removed. broken: x → y"]:
            self.assertFalse(red(text), text)

    def test_a_criterion_whose_every_break_cites_the_close_was_first_broken_at_the_close(self):
        crit = sd.criteria("- [x] C28.1 **hold** — X.\n      broken: the guard removed → 1 of 3 (#40)\n"
                           "- [x] C28.2 **new** — Y.\n      broken: a → b (#40)\n      broken: c → d (#38)\n"
                           "- [x] C28.3 **new** — Z.\n      broken: a → b, as #38 showed\n"
                           "- [x] C28.4 **new** — W. #40\n      broken: none → the grep is the check\n")
        self.assertEqual([c["broke_in"] for c in crit], [[40], [38, 40], [38], []])
        day = dict(prs=[dict(number=38, kind="code"), dict(number=40, kind="close")], evidence=crit)
        # C28.2 was also broken in its track; C28.3 in a track; C28.4 records no break to judge.
        self.assertEqual(sd.broken_at_close(day), ["C28.1"])
        self.assertEqual(sd.broken_at_close(dict(day, prs=day["prs"][:1])), [])

    def test_a_spec_with_no_criterion_tagged_predates_the_evidence_format(self):
        self.assertFalse(sd.in_evidence_format(sd.criteria("- [x] Login returns 200.\n- [x] Logout clears it.\n")))
        self.assertTrue(sd.in_evidence_format(sd.criteria("- [x] Login returns 200.\n- [x] **hold** — X.\n")))
        self.assertTrue(sd.in_evidence_format(sd.criteria(CRITERIA)))

    def test_a_name_not_in_the_tree_when_the_day_ended_is_not_evidence(self):
        self.assertEqual(self.state()[1]["tests"], {"FooIT": "present", "FooIT.saves": "present"})

    def test_a_test_that_leaves_the_tree_or_can_be_skipped_is_reported(self):
        self.repo.merge({"src/FooIT.java": "@Disabled class FooIT { void refuses() {} }\n"})
        self.assertEqual(self.state()[1]["tests"], {"FooIT": "skippable", "FooIT.saves": "missing"})
        self.repo.merge({"src/FooIT.java": ""})
        self.repo.git("rm", "-q", "src/FooIT.java")
        self.repo.git("commit", "-q", "-m", "gone")
        self.repo.snaps.append(dict(self.repo.snaps[-1], sha=self.repo.git("rev-parse", "--short", "HEAD").strip()))
        self.assertEqual(set(self.state()[0]["tests"].values()), {"missing"})

    def test_a_test_moved_under_a_new_name_is_followed_from_the_merge_it_arrives(self):
        # Day 17: SavedJobCountsUnavailableIT left in #174, and its Test arrived in #180. A helper
        # leaving as a test of its name arrives is not a move: only tests are followed.
        self.repo.merge({"src/Stub.java": "class Stub {}\n"})
        self.repo.git("rm", "-q", "src/FooIT.java", "src/Stub.java")
        self.repo.merge({"src/Other.java": "class Other {}\n"})
        self.repo.merge({"svc/FooTest.java": "class FooTest { void refuses() {} void saves() {} }\n",
                         "svc/StubTest.java": "class StubTest {}\n"})
        self.assertEqual(self.repo.inside(lambda blobs: sd.moves(self.repo.snaps)), [(4, "FooIT", "FooTest")])
        self.assertEqual(self.state()[1]["tests"], {"FooIT": "present", "FooIT.saves": "present"})

    def test_a_class_of_the_same_stem_there_before_the_test_left_is_not_where_it_went(self):
        self.repo.merge({"svc/FooTest.java": "class FooTest { void refuses() {} void saves() {} }\n"})
        self.repo.git("rm", "-q", "src/FooIT.java")
        self.repo.merge({"src/Other.java": "class Other {}\n"})
        self.assertEqual(self.repo.inside(lambda blobs: sd.moves(self.repo.snaps)), [])
        self.assertEqual(set(self.state()[1]["tests"].values()), {"missing"})

    def test_a_name_there_before_the_test_left_and_arriving_again_after_is_followed_to_the_later(self):
        # InternalCallsObservedTest: in matching-service from Day 21, then in application-service
        # in #305, after InternalCallsObservedIT left in #296.
        self.repo.merge({"svc/FooTest.java": "class FooTest { void other() {} }\n"})
        self.repo.git("rm", "-q", "src/FooIT.java")
        self.repo.merge({"src/Other.java": "class Other {}\n"})
        self.repo.merge({"app/FooTest.java": "class FooTest { void refuses() {} void saves() {} }\n"})
        self.assertEqual(self.repo.inside(lambda blobs: sd.moves(self.repo.snaps)), [(4, "FooIT", "FooTest")])
        self.assertEqual(self.state()[1]["tests"], {"FooIT": "present", "FooIT.saves": "present"})

    def test_a_move_to_another_stem_is_followed_only_by_the_rename_table(self):
        self.repo.git("rm", "-q", "src/FooIT.java")
        self.repo.merge({"svc/BarTest.java": "class BarTest { void refuses() {} void saves() {} }\n"})
        self.assertEqual(set(self.state()[1]["tests"].values()), {"missing"})
        use_project(self, dict(renamed=[[2, "FooIT", "BarTest"]]))
        self.assertEqual(self.repo.inside(lambda blobs: sd.moves(self.repo.snaps)), [(2, "FooIT", "BarTest")])
        self.assertEqual(self.state()[1]["tests"], {"FooIT": "present", "FooIT.saves": "present"})

    def test_a_test_run_on_a_system_property_is_run_when_ci_passes_it_and_disabled_is_not(self):
        on = '@EnabledIfSystemProperty(named = "harness.gateway", matches = "true")\n'
        self.repo.merge({"src/FooIT.java": on + "class FooIT { void refuses() {} void saves() {} }\n"})
        self.assertEqual(set(self.state()[1]["tests"].values()), {"skippable"})
        self.repo.merge({".github/workflows/ci.yml": "run: ./build verify -Dharness.gateway=false\n"})
        self.assertEqual(set(self.state()[1]["tests"].values()), {"skippable"})
        self.repo.merge({".github/workflows/ci.yml": "run: ./build verify -pl app -am -Dharness.gateway=true\n"})
        self.assertEqual(set(self.state()[1]["tests"].values()), {"present"})
        self.repo.merge({"src/FooIT.java": on + "@Disabled class FooIT { void refuses() {} void saves() {} }\n"})
        self.assertEqual(set(self.state()[1]["tests"].values()), {"skippable"})

    def test_the_history_counts_a_moved_test_missing_until_it_arrives(self):
        days = [dict(day=1, status="done", prs=[dict(number=1)], evidence=sd.criteria(CRITERIA))]
        self.repo.git("rm", "-q", "src/FooIT.java")
        self.repo.merge({"src/Other.java": "class Other {}\n"})
        self.repo.merge({"svc/FooTest.java": "class FooTest { void refuses() {} void saves() {} }\n"})
        rows = [{} for _ in self.repo.snaps]
        self.repo.inside(lambda blobs: sd.evidence_history(rows, sd.evidence(days, self.repo.snaps, blobs),
                                                           self.repo.snaps, blobs))
        self.assertEqual([r["evidence"] for r in rows][1:], [
            dict(present=3, skippable=0, missing=0, retired=0),
            dict(present=0, skippable=0, missing=3, retired=0),
            dict(present=3, skippable=0, missing=0, retired=0)])


    def test_the_history_starts_when_the_day_ends_and_shows_the_merge_a_test_left(self):
        self.repo.merge({"src/FooIT.java": "class FooIT { void refuses() {} }\n"})
        days = [dict(day=1, status="done", prs=[dict(number=1)], evidence=sd.criteria(CRITERIA))]
        rows = [{} for _ in self.repo.snaps]

        def history(blobs):
            sd.evidence_history(rows, sd.evidence(days, self.repo.snaps, blobs), self.repo.snaps, blobs)
        self.repo.inside(history)
        self.assertEqual([r["evidence"] for r in rows], [
            None,
            dict(present=3, skippable=0, missing=0, retired=0),
            dict(present=2, skippable=0, missing=1, retired=0)])

    def history_after_removal(self, spec):
        """Day 1's tests, then a day 2 merge that removes FooIT and writes day 2's spec, as `spec`."""
        days = [dict(day=1, status="done", prs=[dict(number=1)], evidence=sd.criteria(CRITERIA)),
                dict(day=2, file="specs/day-02-y.md", status="done", prs=[dict(number=2)], evidence=[])]
        self.repo.merge({"src/FooIT.java": None, "specs/day-02-y.md": spec})
        self.repo.snaps[-1]["branch"] = "day-02/track-a-x"
        rows = [{} for _ in self.repo.snaps]
        self.repo.inside(lambda blobs: sd.evidence_history(rows, sd.evidence(days, self.repo.snaps, blobs),
                                                           self.repo.snaps, blobs))
        return rows, days

    def test_a_test_a_later_days_spec_names_as_removed_is_retired_not_missing(self):
        rows, days = self.history_after_removal("# Day 02\n\nIt removes `FooIT`.\n")
        self.assertEqual(rows[-1]["evidence"], dict(present=0, skippable=0, missing=0, retired=3))
        self.assertEqual({v for c in days[0]["evidence"] for v in c["tests"].values()}, {"retired"})

    def test_a_test_gone_that_no_later_spec_names_stays_missing(self):
        rows, days = self.history_after_removal("# Day 02\n\nIt removes the rest.\n")
        self.assertEqual(rows[-1]["evidence"], dict(present=0, skippable=0, missing=3, retired=0))
        self.assertEqual({v for c in days[0]["evidence"] for v in c["tests"].values()}, {"missing"})


REMOVALS = """## Acceptance criteria
- [x] **new** — `grep -rn "OldThing\\|old_table" --include=*.java .`
      returns nothing. Red today: two.

## Verify
```bash
cd core
grep -rn "TODO day-01" */src/ || echo "clean"
grep -rn "kept" app/ | wc -l
```

## Notes
- `grep -rn "NotACheck"` returns nothing, but a note is not a check.
"""


class RemovalTest(unittest.TestCase):
    """A day's greps that must print nothing, run at every merge from the day's end."""

    def setUp(self):
        use_project(self, PROJECT)

    def test_the_checks_are_the_criteria_and_verify_greps_that_expect_nothing(self):
        self.assertEqual(sd.removal_checks(REMOVALS), ['grep -rn "OldThing\\|old_table" --include=*.java .',
                                                       'grep -rn "TODO day-01" */src/'])

    def test_a_basic_regex_alternation_is_an_alternation_and_a_bare_bar_is_literal(self):
        rx, paths, include = sd.grep_rule('grep -rn "OldThing\\|old_table" --include=*.java .')
        self.assertEqual((bool(rx.search("old_table")), paths, include), (True, ["."], "*.java"))
        self.assertFalse(sd.grep_rule('grep -rn "a|b" x/')[0].search("a"))
        self.assertTrue(sd.grep_rule('grep -rnE "a|b" x/')[0].search("a"))
        self.assertIsNone(sd.grep_rule('grep -rn "x" a/ | grep -v b'))

    def test_a_check_counts_lines_in_its_scope_from_the_day_it_ended(self):
        repo = Repo().merge({"core/app/A.java": "OldThing a;\nold_table b;\n", "core/app/B.txt": "OldThing\n",
                             "other/C.java": "OldThing c;\n", "core/app/src/D.java": "",
                             "core/pom.txt": "TODO day-01\n"})
        repo.merge({"core/app/A.java": "class A {}\n"})
        repo.merge({"core/app/A.java": "class A { OldThing back; }\n", "core/app/src/D.java": "// TODO day-01\n"})
        def run(ended_at):
            days = [dict(day=1, ended_at=ended_at, removal_checks=sd.removal_checks(REMOVALS))]
            return [(c["base"], c["hits"]) for c in repo.inside(lambda blobs: sd.removal_history(days, repo.snaps, blobs))]
        try:
            # B.txt is not *.java, other/ is not under core/, and pom.txt is not under */src/.
            self.assertEqual(run(0), [("core", [2, 0, 1]), ("core", [0, 0, 1])])
            self.assertEqual(run(1), [("core", [0, 1]), ("core", [0, 1])])
        finally:
            repo.close()

    def test_a_path_follows_a_move_and_a_parent_of_it_also_reads_where_it_went(self):
        moves = [("backend/jobs", "services/orders-service"), ("backend", "services/account-service")]
        self.assertEqual(sd.follow("backend/jobs/src", moves), ["services/orders-service/src"])
        self.assertEqual(sd.follow("backend/docs", moves), ["services/account-service/docs"])
        self.assertEqual(sd.follow("backend/*/src/main", moves),
                         ["services/orders-service/src/main", "services/account-service/*/src/main"])
        self.assertEqual(sd.follow("backend", moves[:1]), ["services/orders-service", "backend"])
        self.assertEqual(sd.follow("docker-compose.yml", moves), ["docker-compose.yml"])

    def test_the_project_files_moves_follow_moved_docs_on_to_docs_system(self):
        moves = [(old, new) for _, old, new in sd.MOVED]
        self.assertEqual(sd.follow("core/docs", moves), ["docs/system"])
        self.assertEqual(sd.follow("core/docs/api.md", moves), ["docs/system/api.md"])

    def test_the_project_files_moves_follow_a_lifted_app_to_the_service_root(self):
        moves = [(old, new) for _, old, new in sd.MOVED]
        self.assertEqual(sd.follow("core/app/src/main/java", moves), ["services/account-service/src/main/java"])
        self.assertEqual(sd.follow("services/account-service/app/src", moves), ["services/account-service/src"])

    def test_a_check_reads_moved_code_counts_its_files_and_lists_its_lines_on_the_last_merge(self):
        repo = Repo().merge({"core/stock/src/A.java": "class A {}\n", "core/app/src/B.java": "class B {}\n"})
        repo.merge({"core/stock/src/A.java": None, "services/stock-service/src/A.java": "// TODO day-01 here\n"})
        repo.merge({"core/app/src/B.java": None, "services/stock-service/src/A.java": "class A {}\n"})
        def run(moved):
            days = [dict(day=1, ended_at=0, removal_checks=sd.removal_checks(REMOVALS))]
            return repo.inside(lambda blobs: sd.removal_history(days, repo.snaps, blobs, moved))[1]
        try:
            # Merge 2's tree has no core/ left: unfollowed, the check reads nothing and passes.
            still = run([])
            self.assertEqual((still["files"], still["hits"]), ([2, 1, 0], [0, 0, 0]))
            followed = run([(1, "core/stock", "services/stock-service")])
            self.assertEqual((followed["files"], followed["hits"], followed["found"]), ([2, 2, 1], [0, 1, 0], []))
            repo.merge({"services/stock-service/src/A.java": "x\n// TODO day-01 again\n"})
            self.assertEqual(run([(1, "core/stock", "services/stock-service")])["found"],
                             [dict(path="services/stock-service/src/A.java", line=2, text="// TODO day-01 again")])
        finally:
            repo.close()


class HandOffTest(unittest.TestCase):
    """What finished days leave to days not yet run, and whether the receiving spec took it."""

    def test_an_excerpt_ends_at_a_word_and_outside_a_code_span(self):
        self.assertEqual(sd.excerpt("alpha  beta\n gamma", 40), "alpha beta gamma")
        self.assertEqual(sd.excerpt("alpha beta gamma", 12), "alpha beta…")
        self.assertEqual(sd.excerpt("see `foo bar baz` now", 12), "see…")

    def test_the_days_a_sentence_names(self):
        self.assertEqual(sd.days_named("Day 17 adds it; Days 18-19 and Days 19, 21 and 24 build theirs"),
                         {17, 18, 19, 21, 24})
        self.assertEqual(sd.days_named("Days 26–28, or Day 30"), {26, 27, 28, 30})

    def test_a_hand_off_is_picked_up_by_the_spec_that_names_its_day_or_its_file(self):
        repo = Repo().merge({
            "specs/day-01-a.md": "## Notes\n- For Day 03: the key.\n- Day 02's findings for Day 04 are there.\n"
                                 "- Day 05 has nothing from this day.\n",
            "specs/day-02-b.md": "# Day 02\n",
            "specs/day-03-c.md": "# Day 03\n\nFrom Day 01: the key.\n",
            "specs/day-04-d.md": "# Day 04\n\nFrom Day 02.\n",
            "specs/day-05-e.md": "# Day 05\n\nIt reads `Foo`.\n",
            "src/Foo.java": "// Day 05 moves this.\nclass Foo {} // Day 05\n",
            "src/Bar.java": "/* Day 04 deletes this. */\n",
        })
        days = [dict(day=n, file=f"specs/day-0{n}-{c}.md", status="done" if n < 3 else "ready")
                for n, c in zip(range(1, 6), "abcde")]
        try:
            found = repo.inside(lambda blobs: sd.hand_offs(days, [1, 2, 3, 4, 5], repo.snaps[-1]["sha"], blobs))
        finally:
            repo.close()
        self.assertEqual([(h["to"], h["source"], h["picked"]) for h in found], [
            (3, "Day 01 Notes", True),          # in run order, open ones first within a day
            (4, "src/Bar.java:1", False),       # Day 04 never names Bar
            (4, "Day 01 Notes", True),          # points to Day 02, which Day 04 names
            (5, "Day 01 Notes", False),
            (5, "src/Foo.java:1", True)])       # the code line after it is not a comment
        self.assertEqual(found[4]["text"], "Day 05 moves this.")

    def test_a_hand_off_with_an_id_is_picked_up_only_by_a_spec_citing_it(self):
        repo = Repo().merge({
            "specs/day-01-a.md": "## Notes\n- **Hand-off** H01.1 → Day 03: the key.\n"
                                 "- **Hand-off** H01.2 → Day 02: the queue.\n"
                                 "- **Hand-off** H01.3 → the maintainer: branch protection.\n"
                                 "- **Hand-off** H01.4 → the maintainer: the volume.\n",
            "specs/day-02-b.md": "# Day 02\n\nFrom Day 01: nothing cited.\n",
            "specs/day-03-c.md": "# Day 03\n\nFrom Day 01: the key.\n\n## Notes\n- H01.4 done by hand.\n",
            "specs/day-04-d.md": "# Day 04\n\nPicks up H01.1.\n",
            "src/Foo.java": "// Day 01 wrote this.\n",
        })
        days = [dict(day=n, file=f"specs/day-0{n}-{c}.md", status="done" if n < 3 else "ready")
                for n, c in zip(range(1, 5), "abcd")]
        try:
            found = repo.inside(lambda blobs: sd.hand_offs(days, [1, 2, 3, 4], repo.snaps[-1]["sha"], blobs))
        finally:
            repo.close()
        self.assertEqual([(h["to"], h["id"], h["picked"]) for h in found], [
            (3, "H01.1", False),                # Day 03 names Day 01, not the ID; Day 04 cites it
            (None, "H01.2", False),             # Day 02 finished without citing it
            (None, "H01.3", False)])            # no day takes it; H01.4 is cited by Day 03's Notes

    def test_a_track_a_pr_announces_that_no_branch_names_is_the_next_step(self):
        prs = [dict(number=298, headRefName="day-25/track-e1b-x", body="**E1c** (next). Not Day 21's E1d; `grep -A3`."),
               dict(number=297, headRefName="day-25/track-e1a-x", body="Track E1 splits; B1 stays."),
               dict(number=290, headRefName="day-25/track-b-x", body="B1 here")]
        self.assertEqual(sd.unopened_tracks(prs), [dict(track="E1c", pr=298)])
        self.assertEqual(sd.unopened_tracks(prs + [dict(number=305, headRefName="day-25/track-e1c-y", body="")]), [])
        day = dict(a_day(25), status="active", prs=[dict(kind="spec")], tracks_merged=["A"],
                   tracks_unopened=sd.unopened_tracks(prs))
        self.assertEqual(sd.next_step([day], [], [25], None), "Day 25 Track E1c: announced in #298, no branch names it")

    def test_a_criterion_id_is_not_a_track(self):
        self.assertEqual(sd.unopened_tracks([dict(number=1, headRefName="day-32/track-c1-x", body="Ticks C32.5 and H32.1.")]), [])

    def test_a_day_numbered_name_is_not_a_track(self):
        body = 'It read `C32.x` as "C32", a track C32: wrong.'
        self.assertEqual(sd.unopened_tracks([dict(number=1, headRefName="day-32/track-c1-x", body=body)]), [])

    def test_a_hand_off_range_names_every_id_in_it(self):
        self.assertEqual(sd.hand_off_ids("H34.1–H34.3 and H35.2-4, H36.7"),
                         {"H34.1", "H34.2", "H34.3", "H35.2", "H35.3", "H35.4", "H36.7"})

    def test_a_hand_off_range_picks_up_each_id_in_it(self):
        repo = Repo().merge({
            "specs/day-01-a.md": "## Notes\n- **Hand-off** H01.2 → the maintainer: the middle one.\n",
            "specs/day-02-b.md": "# Day 02\n\nPicks up H01.1–H01.3.\n",
            "src/App.java": "// Day 01 wrote this.\n",  # git grep fails on a tree with no day in its code
        })
        days = [dict(day=1, file="specs/day-01-a.md", status="done"),
                dict(day=2, file="specs/day-02-b.md", status="ready")]
        try:
            found = repo.inside(lambda blobs: sd.hand_offs(days, [1, 2], repo.snaps[-1]["sha"], blobs))
        finally:
            repo.close()
        self.assertEqual(found, [])  # Day 02's range cites H01.2, so no hand-off is left open

    def test_a_code_comment_is_not_handed_to_the_day_whose_pr_wrote_it(self):
        repo = Repo().merge({
            "specs/day-01-a.md": "# Day 01\n",
            "specs/day-02-b.md": "# Day 02\n",
            "specs/day-03-c.md": "# Day 03\n",
            "src/Foo.java": "// Day 02 finishes this.\n// Day 03 removes this.\n",
        })
        repo.git("commit", "--amend", "-q", "-m", "Merge pull request #7 from o/day-02/track-a-x")
        repo.snaps[-1]["sha"] = repo.git("rev-parse", "--short", "HEAD").strip()
        days = [dict(day=n, file=f"specs/day-0{n}-{c}.md", status="done" if n < 2 else "ready")
                for n, c in zip(range(1, 4), "abc")]
        try:
            found = repo.inside(lambda blobs: sd.hand_offs(days, [1, 2, 3], repo.snaps[-1]["sha"], blobs))
        finally:
            repo.close()
        self.assertEqual([(h["to"], h["source"]) for h in found], [(3, "src/Foo.java:2")])


class ProjectFileTest(unittest.TestCase):
    """spec-drift.config.json: what git cannot tell about a repository, empty in a new one."""

    def test_with_no_file_or_no_field_nothing_is_set_and_verify_reads_the_root(self):
        for fields in (None, {}):
            folder = tempfile.mkdtemp(prefix="spec-drift-config-")
            self.addCleanup(shutil.rmtree, folder, True)
            path = os.path.join(folder, "spec-drift.config.json")
            if fields is not None:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(fields, f)
            c = sd.project_config(path)
            self.assertEqual((c["RENAMED"], c["MOVED"], c["VERIFY_BASES"], c["SERVICE"], c["INFRA_WORKFLOW"]),
                             ({}, [], ("",), {}, ""))

    def test_renames_moves_and_verify_bases_are_the_files(self):
        use_project(self, PROJECT)
        self.assertEqual(sd.RENAMED, {296: ("OrdersUserDeletedConsumerIT", "UserDeletedConsumerTest"),
                                      298: ("CircuitBreakerIT", "StockLookupBreakerTest")})
        self.assertEqual(len(sd.MOVED), 6)
        self.assertEqual(sd.MOVED[3], (315, "core", "services/account-service"))
        self.assertEqual(sd.VERIFY_BASES, ("core", ""))

    def test_boundaries_place_and_cross_the_files_services_under_its_package_root(self):
        root = "src/main/java/org/example/shop"
        repo = Repo().merge({
            f"core/{root}/orders/Order.java": "import org.example.shop.auth.User;\n"
                                               "import org.example.shop.util.Text;\nclass Order {}\n",
            f"core/{root}/util/Text.java": "class Text {}\n",
            f"services/stock-service/{root}/catalog/Item.java": "import static org.example.shop.orders.Order.x;\n"
                                                                 "class Item {}\n",
            f"core/src/test/java/org/example/shop/orders/OrderTest.java": "import org.example.shop.auth.User;\n"})
        self.addCleanup(repo.close)
        def boundaries():
            rows = [{}]
            repo.inside(lambda blobs: sd.boundaries(rows, repo.snaps, blobs))
            return rows[0]["placed"], rows[0]["crossings"]
        use_project(self, PROJECT)
        self.assertEqual(boundaries(), ({"orders": [3, 0], "stock": [0, 2]}, {"orders>account": 1, "stock>orders": 1}))
        use_project(self, {})
        self.assertEqual(boundaries(), ({}, {}))

    def test_the_infra_workflow_is_the_files_and_with_none_gh_is_not_asked(self):
        asked, real = [], sd.run
        self.addCleanup(setattr, sd, "run", real)
        sd.run = lambda *args: asked.append(args) or "[]"
        use_project(self, PROJECT)
        sd.infra(sd.INFRA_WORKFLOW)
        self.assertEqual([a[:5] for a in asked], [("gh", "run", "list", "--workflow", "infra.yaml")])
        use_project(self, {})
        asked.clear()
        self.assertEqual((sd.infra(sd.INFRA_WORKFLOW), asked), (dict(runs=[], latest=None), []))


class OwnerAndCaveatTest(unittest.TestCase):
    """Only the owner's PRs are read (SO-12), and the dashboard says what name coverage cannot see."""

    def test_only_the_owners_prs_are_kept(self):
        listed = [dict(number=1, author=dict(login="Yusuprozimemet")),
                  dict(number=2, author=dict(login="app/dependabot")),
                  dict(number=3)]
        self.assertEqual([p["number"] for p in sd.owners_prs(listed, "Yusuprozimemet")], [1])

    def test_another_authors_pr_is_not_the_next_step(self):
        mine = dict(number=50, title="Day 25 track A", state="OPEN", author=dict(login="Yusuprozimemet"))
        theirs = dict(number=51, title="Bump x", state="OPEN", author=dict(login="app/dependabot"))
        day = a_day(25, kinds=["spec"])
        everyone = sd.next_step([day], [mine, theirs], [25], None)
        mine_only = [p for p in sd.owners_prs([mine, theirs], "Yusuprozimemet") if p["state"] == "OPEN"]
        self.assertIn("#51", everyone)
        self.assertEqual(sd.next_step([day], mine_only, [25], None), "Waiting on #50 Day 25 track A")

    def test_another_authors_body_names_no_track(self):
        theirs = dict(number=51, headRefName="day-25/track-e1a-x", title="x", body="Ticks E1c.",
                      author=dict(login="app/dependabot"))
        self.assertEqual(sd.unopened_tracks([theirs]), [dict(track="E1c", pr=51)])
        self.assertEqual(sd.unopened_tracks(sd.owners_prs([theirs], "Yusuprozimemet")), [])

    def test_the_coverage_caveat_says_tests_and_tooling_count_and_cites_no_measurement(self):
        self.assertIn("Name coverage counts test and tooling files as code.", sd.CAVEATS)
        for c in sd.CAVEATS:  # another project has no such audit, file or figure
            self.assertNotRegex(c, r"\d|\.md\b", c)

    def test_the_project_is_the_repositorys_name_or_with_no_remote_its_folders(self):
        def fake(*args):
            if args[:3] == ("gh", "repo", "view"):
                if remote:
                    return "toy-repo\n"
                raise subprocess.CalledProcessError(1, args, stderr="no git remotes found")
            if args[:2] == ("git", "rev-parse"):
                return "/home/someone/toy-folder\n"
        real = sd.run
        try:
            sd.run = fake
            remote = True
            self.assertEqual(sd.project_name(), "toy-repo")
            remote = False
            self.assertEqual(sd.project_name(), "toy-folder")
        finally:
            sd.run = real


# Boots docs/dashboard/dashboard.js on the data from stdin, with a document that accepts anything,
# and prints the eyebrow and the stats it wrote. The panels drawn after the eyebrow may throw on a
# small fixture; only an error before it fails a test.
BOOT = r"""
const fs = require("fs"), vm = require("vm"), els = {};
const stub = () => new Proxy(function () {}, {
  get: (t, k) => k === Symbol.toPrimitive ? () => "" : k === Symbol.iterator ? [][Symbol.iterator] : k in t ? t[k] : (t[k] = stub()),
  apply: () => stub(), construct: () => stub() });
const document = new Proxy({}, { get: (t, k) => k === "getElementById" ? id => els[id] || (els[id] = stub()) : stub() });
const ctx = vm.createContext({ document, window: {}, DATA: JSON.parse(fs.readFileSync(0, "utf8")) });
let error = null;
try { vm.runInContext(fs.readFileSync(process.argv[1], "utf8") + "\nboot(DATA);", ctx); } catch (e) { error = e.message; }
const text = id => els[id] ? [els[id].textContent, els[id].innerHTML].find(v => typeof v === "string") : null;
console.log(JSON.stringify({ eyebrow: text("eyebrow"), stats: text("stats"), error }));
"""


def page_row(i, pr, kind, gap):
    return dict(i=i, sha=f"{i:07x}", date="2026-01-01", pr=pr, title="t", kind=kind, gap_full=gap)


def page(rows, days=(), order=(), current_day=None):
    """What the page writes for this data: its eyebrow, and the value under a stat's name."""
    data = dict(now=dict(generated="2026-01-01T00:00", head="abc", last_pr=None, current_day=current_day,
                         next_step="x", open_prs=[]), rows=rows, days=list(days), order=list(order))
    out = json.loads(subprocess.run(["node", "-e", BOOT, os.path.join(HERE, "..", "docs", "dashboard", "dashboard.js")],
                                    input=json.dumps(data), capture_output=True, encoding="utf-8", check=True).stdout)
    if out["eyebrow"] is None:
        raise AssertionError(f"the page stopped before the eyebrow: {out['error']}")
    stat = lambda name: out["stats"].split(f">{name}</span>")[1].split('class="v num">')[1].split("<")[0]
    return out["eyebrow"], stat


# Boots the page on a document whose elements keep what is drawn into them, and prints each box's
# HTML, SVG included, the error that stopped the page, if one did, and what went to console.error.
DRAW = r"""
const fs = require("fs"), vm = require("vm"), els = {}, logged = [];
class El {
  constructor(tag) { this.tag = tag; this.attrs = {}; this.kids = []; this.html = ""; this.style = {}; this.dataset = {}; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  appendChild(c) { this.kids.push(c); return c; }
  set innerHTML(h) { this.html = String(h); this.kids = []; }
  get innerHTML() { return this.html + this.kids.map(k => k.out()).join(""); }
  set textContent(t) { this.innerHTML = t; }
  get textContent() { return this.html; }
  insertAdjacentHTML(_, h) { this.kids.push({ out: () => String(h) }); }
  addEventListener() {} querySelectorAll() { return []; }
  out() { return `<${this.tag}${Object.entries(this.attrs).map(([k, v]) => ` ${k}="${v}"`).join("")}>${this.innerHTML}</${this.tag}>`; }
}
const document = { getElementById: id => els[id] || (els[id] = new El("div")), createElementNS: (_, t) => new El(t),
  querySelectorAll: () => [] };
const ctx = vm.createContext({ document, window: {}, matchMedia: () => ({ matches: true }), DATA: JSON.parse(fs.readFileSync(0, "utf8")),
  console: { error: e => logged.push(String(e && e.message || e)) } });
let error = null;
try { vm.runInContext(fs.readFileSync(process.argv[1], "utf8") + "\nboot(DATA);", ctx); } catch (e) { error = e.message; }
console.log(JSON.stringify({ error, logged, panels: Object.fromEntries(Object.entries(els).map(([k, e]) => [k, e.innerHTML])) }));
"""


def page_data(rows, days=(), order=(), **more):
    """The data the page draws: these rows, days and run order, empty elsewhere; `more` replaces fields."""
    data = dict(now=dict(generated="2026-01-01T00:00", head="abc", last_pr=None, current_day=None,
                         next_step="x", open_prs=[]), rows=list(rows), days=list(days), order=list(order),
                files=[], removals=[], hand_offs=[], tokens=[], verification=[], infra=dict(runs=[], latest=None),
                deployment=None, conclusion=dict(reads=[], measured=[]), origin_lines=0, vocab_size=0)
    data.update(more)
    return data


def drawn(rows=(), days=(), order=(), page=None, **more):
    """The error that stopped the page, or None, the HTML each box holds, and what was logged as an
    error; `more` replaces fields of the data. With `page`, a page spec-drift.py --build wrote: its
    inlined script draws its own data, and the other arguments are not used."""
    data = page_data(rows, days, order, **more)
    script = os.path.join(HERE, "..", "docs", "dashboard", "dashboard.js")
    with tempfile.TemporaryDirectory() as tmp:
        if page:
            with open(page, encoding="utf-8") as f:
                html = f.read()
            # build() inlines dashboard.js as the script that defines boot(); fill() escapes "</" as "<\/",
            # which JSON reads back as "/".
            script = os.path.join(tmp, "dashboard.js")
            with open(script, "w", encoding="utf-8") as f:
                f.write(next(s for s in re.findall(r"<script>\n(.*?)</script>", html, re.S) if "function boot(" in s))
            data = json.loads(re.search(r"^window\.SPEC_DRIFT = (.*);$", html, re.M).group(1))
        out = json.loads(subprocess.run(["node", "-e", DRAW, script], input=json.dumps(data),
                                        capture_output=True, encoding="utf-8", check=True).stdout)
    return out["error"], out["panels"], out["logged"]


class PageProseTest(unittest.TestCase):
    """The words around the panels: the page explains any project's data, not the one it was built on."""

    # What the prose said of the project it was built on: its services and layout, its days, PRs and criteria, its cloud.
    MARKERS = ["monolith", "identity", "job-service", "backend/", "saved_jobs", "SavedJobCounts", "GatewayHarnessIT",
               "infra-ci", "Terraform", "LocalStack", "AWS", "Day 35", "Days 1–4", "Days 38–40", "C35.16", "H28.1",
               "#55", "#298", "#310"]

    def test_the_prose_names_none_of_the_project_it_was_built_on(self):
        with open(os.path.join(HERE, "..", "docs", "dashboard", "index.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertEqual([m for m in self.MARKERS if m in page], [])

    def test_every_script_it_names_is_in_the_repository(self):
        # The deployment panel named scripts/live-checks.py after it moved out with the source project's data.
        with open(os.path.join(HERE, "..", "docs", "dashboard", "index.html"), encoding="utf-8") as f:
            named = re.findall(r"<code>([\w.-]+/[\w./-]+\.py)</code>", f.read())  # a path, not a name like conftest.py
        self.assertEqual([p for p in named if not os.path.exists(os.path.join(HERE, "..", p))], [])
        self.assertIn("scripts/token-usage.py", named)  # the pattern still finds what the prose names


@unittest.skipUnless(shutil.which("node"), "needs node")
class PageTest(unittest.TestCase):
    """The page's own counts, on a new repository: direct commits, flat gaps, days without specs."""

    def test_merged_prs_are_the_merges_that_name_a_pr(self):
        # The kit's main: direct commits, then PR merges. Each commit is a row; only a PR merge counts.
        rows = [page_row(0, None, "origin", 50), page_row(1, None, "origin", 50), page_row(2, 1, "other", 50),
                page_row(3, None, "origin", 50), page_row(4, 2, "other", 50)]
        self.assertEqual(page(rows)[0].split(" · ", 1)[1], "between days · 2 merged PRs")

    def test_the_gap_share_leaves_out_direct_commits_and_is_a_dash_with_no_gap_closed(self):
        # A direct commit closes 10°, a spec PR widens 5°, a code PR closes 10°: the PRs closed 5°,
        # and the spec's share of it is -5 / 5. Counting the direct commit would make it -5 / 15.
        moved = [page_row(0, None, "origin", 50), page_row(1, None, "origin", 40), page_row(2, 1, "spec", 45),
                 page_row(3, 2, "code", 35)]
        self.assertEqual(page(moved)[1]("Share of the gap closed by the spec"), "-100%")
        flat = [page_row(0, None, "origin", 70.8), page_row(1, None, "origin", 70.8), page_row(2, 1, "other", 70.8)]
        self.assertEqual(page(flat)[1]("Share of the gap closed by the spec"), "–")

    def test_the_day_total_is_the_run_order_and_the_cut_days_with_specs(self):
        # Specs for Days 12 and 36 and a cut Day 29; plan.md runs 12, 18, 17, 36 and 40.
        days = [dict(a_day(12), status="active", phase=1, title="t", prs=[]), dict(a_day(36), status="ready"),
                dict(a_day(29), status="cut")]
        eyebrow, _ = page([page_row(0, None, "origin", 50)], days, [12, 18, 17, 36, 40], current_day=12)
        self.assertIn("· Day 12 of 6 ·", eyebrow)

    def test_a_short_history_draws_every_panel_or_says_why_not(self):
        # The kit's main: direct commits, then PRs on no day branch; a flat gap, no service code,
        # 54 test lines and no production lines, and two specs whose days have no PRs.
        rows = [dict(page_row(i, pr, "other" if pr else "origin", 70.8), work=dict(test=27 * i), code_churn=27)
                for i, pr in enumerate([None, None, 1, 2])]
        days = [dict(a_day(n), status="ready", phase=1, title="t", prs=[]) for n in (12, 36)]
        error, panels, _ = drawn(rows, days, [12, 36])
        self.assertIsNone(error)
        for box in ("deltas", "churn", "heat"):  # what each merge did to the gap; spec and code; corrections
            self.assertIn("<svg", panels[box], box)
        for box, why in (("moved", "No service code yet"), ("test-ratio", "No ratio yet"),
                         ("perday", "No day has a merged pull request yet")):
            self.assertIn(f'<p class="load-error">{why}', panels[box], box)

    def test_a_panel_that_throws_says_so_and_the_panels_after_it_still_draw(self):
        # Verification that is not a list: its panel, fourth of boot()'s twelve, throws.
        rows = [dict(page_row(i, pr, "other" if pr else "origin", 70.8), work=dict(test=27 * i), code_churn=27)
                for i, pr in enumerate([None, None, 1, 2])]
        days = [dict(a_day(n), status="ready", phase=1, title="t", prs=[]) for n in (12, 36)]
        error, panels, logged = drawn(rows, days, [12, 36], verification={"kind": "code"})
        self.assertIsNone(error)
        self.assertEqual(panels["breaks"], '<p class="load-error">This panel failed: V.filter is not a function</p>')
        self.assertEqual(logged, ["V.filter is not a function"])
        for box in ("infra-head", "token-bars", "findings", "tbl", "deltas", "heat"):  # after it in boot(), then setSel()
            self.assertTrue(panels[box], box)
            self.assertNotIn("This panel failed", panels[box], box)

    def test_the_boxes_words_name_no_project(self):
        # The first merge; one service still in place and one part out; a day before the evidence
        # format; no infra summary yet. Then no service code at all.
        row = dict(page_row(0, None, "origin", 50), code_churn=0, placed={"billing": [120, 0], "orders": [30, 40]})
        day = dict(a_day(5), status="done", phase=1, title="t", prs=[], evidence_format=False,
                   evidence=[dict(ticked=True, prs=[], tests={}, claim="c")])
        error, panels, _ = drawn([row], [day], [5])
        self.assertIsNone(error)
        self.assertEqual(panels["placed"].split(": ", 1)[1],
                         "<b>billing</b> in place (120 lines) · <b>orders</b> 40 lines out, 30 still in place</p>")
        self.assertIn("Starting point: the code and the plan written for it.", panels["readout"])
        self.assertIn('<tr title="Spec written before the evidence format">', panels["evidence"])
        self.assertEqual(panels["infra-head"], '<p class="load-error">No infra summary on main yet: '
                                               'it appears after the infra workflow next runs on main.</p>')
        _, panels, _ = drawn([page_row(0, None, "origin", 50)])
        self.assertIn("No service code yet: the share counts the packages under <code>services</code> in "
                      "<code>spec-drift.config.json</code>, and the code has none.", panels["moved"])

    def test_with_nothing_deployed_the_panel_names_the_file_and_no_script(self):
        # The live check is the project's own; the source project's moved out with its data.
        error, panels, _ = drawn([page_row(0, None, "origin", 50)], deployment=None)
        self.assertIsNone(error)
        self.assertEqual(panels["deployment-head"], '<p class="load-error">Nothing deployed yet: the panel fills when '
                                                    'a live check has written docs/dashboard/deployment.json.</p>')
        self.assertEqual(panels["deployment-checks"], "")

    def test_the_name_phases_and_stops_come_from_the_data(self):
        days = [dict(a_day(n), status="ready", phase=p, title="t", prs=[]) for n, p in ((1, 0), (2, 0), (3, 1))]
        meta = dict(project="toy-repo", phases=["Lay the ground", "<name>"], stops=[2])
        _, panels, _ = drawn([page_row(0, None, "origin", 50)], days, [1, 2, 3], meta=meta)
        self.assertTrue(panels["eyebrow"].startswith("toy-repo · "), panels["eyebrow"])
        self.assertIn("<b>0. Lay the ground</b>", panels["roadmap"])
        self.assertIn("<b>1. &lt;name&gt;</b>", panels["roadmap"])  # a heading the template left unfilled
        stopped = re.findall(r'class="tile ready stop" data-day="(\d+)"', panels["roadmap"])
        self.assertEqual(stopped, ["2"])

    def test_a_built_page_draws_the_data_inlined_in_it(self):
        # What --build writes: dashboard.js and the data in one file. fill() writes a title's "</" as "<\/".
        rows = [dict(page_row(i, pr, "other" if pr else "origin", 70.8), work=dict(test=27 * i), code_churn=27)
                for i, pr in enumerate([None, None, 1, 2])]
        now = dict(generated="2026-01-01T00:00", head="abc", last_pr=2, current_day=None, next_step="x",
                   open_prs=[dict(number=3, title="Stop at </script> here", url="u")])
        more = dict(now=now, meta=dict(project="toy-repo", phases=["<name>"], stops=[]))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "index.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(sd.build(json.dumps(page_data(rows, **more))))
            built = drawn(page=path)
        self.assertEqual(built, drawn(rows, **more))
        error, panels, logged = built
        self.assertEqual((error, logged), (None, []))
        self.assertTrue(panels["eyebrow"].startswith("toy-repo · "), panels["eyebrow"])
        self.assertEqual([k for k, v in panels.items() if "Stop at &lt;/script&gt; here" in v], ["today"])

    def test_the_break_panel_names_the_first_pr_only_when_there_is_one(self):
        # Two code PRs, one recorded and one silent; the source project also had one before its #310.
        rows = [dict(page_row(i, pr, "other" if pr else "origin", 70.8), work=dict(test=27 * i), code_churn=27)
                for i, pr in enumerate([None, None, 1, 2])]
        pr = lambda n, breaks: dict(number=n, day=None, kind="code", breaks=breaks, pushes=1, failed=0, failed_in=[])
        new = [pr(1, "recorded"), pr(2, "silent")]
        _, panels, _ = drawn(rows, verification=new, meta=dict(break_line_from_pr=0))
        self.assertTrue(panels["breaks"].startswith("<p>1 of 2 code PRs record a break on purpose; 1 silent.</p><ul>"),
                        panels["breaks"])
        self.assertNotIn("not measured", panels["breaks"])
        _, panels, _ = drawn(rows, verification=[pr(309, "not measured")] + new, meta=dict(break_line_from_pr=310))
        self.assertTrue(panels["breaks"].startswith("<p>Since #310, 1 of 2 code PRs"), panels["breaks"])
        self.assertIn("1 code PRs before #310 are not measured.", panels["breaks"])

    @unittest.skipUnless(os.path.exists(COMPARE), "kit/ removed")
    def test_the_source_projects_data_draws_the_boxes_it_drew(self):
        # kit/compare-page.py: the source project's published data through this page, against its saved 53 boxes.
        run = subprocess.run([sys.executable, COMPARE], capture_output=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


def a_day(n, ticked=1, total=1, kinds=(), titles=()):
    return dict(day=n, status="provisional", criteria=dict(ticked=ticked, total=total),
                prs=[dict(kind=k, title=t) for k, t in zip(kinds, list(titles) + [""] * len(kinds))],
                tracks=["A"], tracks_merged=[], track_work={"A": "work"})


class RoadmapTest(unittest.TestCase):
    """Where the dashboard says the work is: the run order plan.md gives, and what counts as done."""

    PLAN = """## Day-by-day specs

Days keep their numbers; they run in this order:

1. The record fix and the platform step (new day specs, numbered from 38).
2. Phase 3: Days 18, 19, 17, 20.
3. Phase 4: the profile endpoint out of Day 24 first, then Days 21, 22, 23, the rest of 24.
4. Phase 5: Days 26, 27, 25, 28. **Stop and evaluate.**
5. Phases 6–7 (Days 29–37): rewritten after the evaluation, or not started.
"""

    def test_a_spec_change_must_touch_a_spec(self):
        self.assertEqual(sd.kind("Spec change: every criterion is new or hold", "specs/criterion-kinds",
                                 ["specs/README.md", "specs/_template.md"]), "other")
        self.assertEqual(sd.kind("Day 16 spec change: checks", "day-16/spec-x", ["specs/day-16-cutover.md"]), "spec")
        self.assertEqual(sd.kind("Plan change: seam first", "plan/course", ["plan.md"]), "spec")
        self.assertEqual(sd.kind("Add spec-drift.py", "tooling/spec-drift-script", []), "other")

    def test_code_is_a_track_and_an_early_day_has_no_exception(self):
        self.assertEqual(sd.kind("Day 01 track A: the harness", "day-01/track-a-harness"), "code")
        self.assertEqual(sd.kind("Day 01: the harness", "day-01/harness"), "other")
        self.assertEqual(sd.kind("Day 02: a fix", "day-02/fix"), "other")

    def test_a_commit_with_no_pr_keeps_its_subject_and_a_repo_without_main_says_so(self):
        repo = Repo().merge({"plan.md": "# Plan\n"})
        self.addCleanup(repo.close)
        repo.git("commit", "--amend", "-q", "-m", "Start the toy project")
        repo.git("branch", "-M", "trunk")
        try:
            said = repo.inside(lambda blobs: sd.snapshots({}))
        except SystemExit as e:
            said = str(e)
        except subprocess.CalledProcessError as e:
            said = f"git exited {e.returncode}"
        self.assertEqual(said, "spec-drift.py reads the branch main, and this repository has none: git branch -m main")
        repo.git("branch", "-M", "main")
        snaps = repo.inside(lambda blobs: sd.snapshots({}))
        self.assertEqual([(s["pr"], s["title"]) for s in snaps], [(None, "Start the toy project")])

    def test_phases_are_the_plans_headings_and_stops_the_days_its_list_marks(self):
        plan = """# Toy plan

### Phase 0 — Lay the ground
### Phase 2 – Build it (later)

## Day-by-day specs

1. Phase 0: Days 3, 1, 2. **Stop and evaluate.**
2. Phase 2: Days 4-6. **Stop and evaluate.**
3. Phase 2: Day 7.

## Course correction after Phase 0

Go on.
"""
        self.assertEqual(sd.phases(plan), ["Lay the ground", "", "Build it (later)"])
        self.assertEqual(sd.stops(plan), [2, 6])  # Day 2's stop, lifted since, is still marked
        self.assertEqual(sd.run_order(plan, list(range(1, 8)))[1], 6)
        self.assertEqual((sd.phases("# Plan\n"), sd.stops("# Plan\n")), ([], []))

    def test_the_plan_templates_list_marks_its_stop_once_filled(self):
        with open(os.path.join(HERE, "..", "plan.md"), encoding="utf-8") as f:
            plan = f.read()
        if not plan.startswith("# <Project> plan"):
            self.skipTest("plan.md is filled in")
        self.assertEqual((sd.phases(plan), sd.stops(plan)), (["<name>", "<name>"], []))  # no day yet
        filled = plan.replace("Days <NN>, <NN>.", "Days 1, 2.").replace("Days <NN>-<NN>.", "Days 3-5.")
        self.assertEqual((sd.stops(filled), sd.run_order(filled, [])), ([2], ([1, 2, 3, 4, 5], 2)))

    def test_the_run_order_is_the_plans(self):
        order, stop = sd.run_order(self.PLAN, list(range(1, 38)))
        self.assertEqual(order[:17], list(range(1, 17)) + [sd.PLATFORM])
        self.assertEqual(order[17:29], [18, 19, 17, 20, 21, 22, 23, 24, 26, 27, 25, 28])
        self.assertEqual(order[29:], list(range(29, 38)))
        self.assertEqual(stop, 28)
        self.assertEqual(sd.run_order(self.PLAN, list(range(1, 40)))[0][16:18], [38, 39])

    def test_a_day_under_10_is_a_day_and_only_a_phase_number_is_not(self):
        plan = "## Day-by-day specs\n\n1. Phase 0: Days 3, 1, 2. **Stop and evaluate.**\n2. Phase 1: Days 4-5.\n"
        self.assertEqual(sd.run_order(plan, [1, 2, 3, 4, 5]), ([3, 1, 2, 4, 5], 2))

    def test_the_source_projects_plan_runs_in_its_order(self):
        # The source project's list as it ended: phase numbers inside words and after "after".
        plan = """## Day-by-day specs

1. The record fix and the platform step (new day specs, numbered from 38).
2. Phase 3: Days 18, 19, 17, 20.
3. Phase 4: Day 41 (the profile endpoint and user id, split out of Day 24) first, then Days 21, 22
   (no dual write), 23, 24.
4. Phase 5: Days 26, 27, 25, 28. **Stop and evaluate.**
5. The cleanup day (course correction after Phase 5), Day 42; done.
6. Phase 7 for the cloud, in this order: Days 32, 33 (the code before the cloud), 36 (the services in
   the cloud), 34, 35; done.
7. Phase 6 (Days 29–31): **cut** after Phase 7 (*Phase 7 outcome*).
8. The close-out day, Day 43: the end-of-Phase-7 audits' findings; done.

## Course correction after Phase 5

The cleanup day first.
"""
        specs = list(range(1, 37)) + list(range(38, 44))  # its specs: no Day 37; Days 29-31 written, then cut
        order, stop = sd.run_order(plan, specs)
        self.assertEqual(order, list(range(1, 17)) + [38, 39, 40, 18, 19, 17, 20, 41, 21, 22, 23, 24, 26, 27, 25, 28,
                                                      42, 32, 33, 36, 34, 35, 43])
        self.assertIsNone(stop)

    def test_the_days_out_of_order_are_those_that_break_the_rising_run(self):
        order = list(range(1, 17)) + [38, 39, 40, 18, 19, 17, 20, 21, 26, 27, 25, 28, sd.PLATFORM]
        self.assertEqual(sd.out_of_order(order), [38, 39, 40, 17, 25])
        self.assertEqual(sd.out_of_order(list(range(1, 10))), [])
        self.assertEqual(sd.out_of_order([]), [])

    def test_a_plan_and_its_specs_parse(self):
        root = tempfile.mkdtemp()
        os.mkdir(os.path.join(root, "specs"))
        for n in range(10, 19):
            open(os.path.join(root, "specs", f"day-{n}-x.md"), "w").close()
        with open(os.path.join(root, "plan.md"), "w", encoding="utf-8") as f:
            f.write("## Day-by-day specs\n\n1. Phase 2: Days 12, 11, 13.\n"
                    "2. Phase 3: Days 14, 15. **Stop and evaluate.**\n3. Phase 4 (Days 16–17): **cut**.\n"
                    "4. Phase 5: Day 18.\n\n## Course correction after Phase 3\n\nGo on.\n")
        with open(os.path.join(root, "plan.md"), encoding="utf-8") as f:
            plan = f.read()
        days = sorted({sd.day_of(n) for n in os.listdir(os.path.join(root, "specs")) if sd.day_of(n)})
        order, stop = sd.run_order(plan, days)
        self.assertEqual(sorted(d for d in order if d not in sd.PLACEHOLDERS), [d for d in days if d not in (16, 17)])
        self.assertIsNone(stop)  # evaluated: the plan has the course correction after Phase 3

    def test_the_cleanup_day_comes_after_the_stop_once_it_is_evaluated(self):
        plan = self.PLAN.replace("5. Phases 6–7 (Days 29–37): rewritten after the evaluation, or not started.",
                                 "5. The cleanup day: its spec is written next, numbered\n"
                                 "   after the last.\n"
                                 "6. Phases 6–7 (Days 29–37).") + "\n## Course correction after Phase 5\n\nCleanup first.\n"
        order, stop = sd.run_order(plan, list(range(1, 39)))
        self.assertIsNone(stop)
        self.assertEqual(order[order.index(28) + 1], sd.CLEANUP)
        days = sd.settle([a_day(28, kinds=["close"]), a_day(29)], [28, sd.CLEANUP, 29])
        self.assertEqual(sd.next_step(days, [], [28, sd.CLEANUP, 29], None, sd.unwritten_lines(plan)),
                         'Day 30: write its day spec (plan.md: "The cleanup day: its spec is written next, numbered after the last.")')
        days[0]["phase"], days[1]["phase"] = 5, 6
        self.assertEqual(sd.unwritten(days, [28, sd.CLEANUP, 29]),
                         dict(day=30, phase=5, title="The cleanup day"))  # the roadmap shows it after Day 28
        self.assertIsNone(sd.unwritten(days, [28, 29]))
        order, _ = sd.run_order(plan, list(range(1, 40)))
        self.assertEqual(order[order.index(28) + 1], 39)  # written: the day takes the placeholder's place
        self.assertEqual(sd.run_order(plan.split("\n## Course correction")[0], list(range(1, 42)))[1], 28)

    def test_a_cut_phase_leaves_the_order_and_the_close_out_day_comes_last(self):
        plan = self.PLAN.replace("5. Phases 6–7 (Days 29–37): rewritten after the evaluation, or not started.",
                                 "5. Phase 7: Days 32-35.\n"
                                 "6. Phase 6 (Days 29–31): **cut** after Phase 7.\n"
                                 "7. The close-out day, numbered after the last.") + "\n## Course correction after Phase 5\n"
        order, stop = sd.run_order(plan, list(range(1, 36)))
        self.assertNotIn(29, order)  # not first, as a day the list does not name would be
        self.assertEqual(order[-2:], [35, sd.CLOSEOUT])
        days = sd.settle([a_day(35, kinds=["close"]), a_day(36)], [35, sd.CLOSEOUT])
        days[0]["phase"] = 7
        self.assertEqual(sd.next_step(days, [], [35, sd.CLOSEOUT], None, sd.unwritten_lines(plan)),
                         'Day 37: write its day spec (plan.md: "The close-out day, numbered after the last.")')
        self.assertEqual(sd.unwritten(days, [35, sd.CLOSEOUT]), dict(day=37, phase=7, title="The close-out day"))
        order, _ = sd.run_order(plan, list(range(1, 36)) + [39])  # after the last named, Day 38
        self.assertEqual(order[-1], 39)  # written: the day takes the placeholder's place
        self.assertEqual(sd.run_order(plan.replace("**cut**", "cut"), list(range(1, 36)))[0][-4:-1], [29, 30, 31])

    def test_a_higher_number_does_not_finish_a_day_that_runs_later(self):
        days = sd.settle([a_day(17), a_day(18, kinds=["code"])], [18, 17])
        self.assertEqual([d["status"] for d in days], ["provisional", "active"])  # 17 waits for 18

    def test_a_planned_day_without_a_spec_is_next_to_write(self):
        plan = "## Day-by-day specs\n\n1. Phase 1: Days 10-12.\n"
        order, _ = sd.run_order(plan, [10, 12])
        self.assertEqual(order, [10, 11, 12])  # plan.md lists Day 11; specs/ has no file for it
        days = sd.settle([a_day(10), a_day(12)], order)
        self.assertEqual(sd.next_step(days, [], order, None),
                         "Day 10: read the spec against the code, then the spec-change PR")  # as before
        days = sd.settle([a_day(10, kinds=["close"]), a_day(12)], order)
        self.assertEqual([d["status"] for d in days], ["done", "provisional"])  # none active: between days
        self.assertEqual(sd.next_step(days, [], order, None),
                         "Day 11: write its day spec (plan.md lists it, specs/ has none)")

    def test_an_unwritten_day_quotes_the_plan_item_it_comes_from(self):
        plan = ("## Day-by-day specs\n\n1. Phase 1: Days 1-2.\n2. A step the plan adds, numbered\n"
                "   from 20.\n3. One more day, numbered after the last.\n")
        self.assertEqual(sd.unwritten_lines(plan), {sd.PLATFORM: "A step the plan adds, numbered from 20.",
                                                    sd.CLEANUP: "One more day, numbered after the last."})
        order, _ = sd.run_order(plan, [1, 2])
        days = sd.settle([a_day(1, kinds=["close"]), a_day(2, kinds=["close"])], order)
        self.assertEqual(sd.next_step(days, [], order, None, sd.unwritten_lines(plan)),
                         'Day 20: write its day spec (plan.md: "A step the plan adds, numbered from 20.")')
        order, _ = sd.run_order(plan, [1, 2, 20])
        days = sd.settle([a_day(1, kinds=["close"]), a_day(2, kinds=["close"]), a_day(20, kinds=["close"])], order)
        self.assertEqual(sd.next_step(days, [], order, None, sd.unwritten_lines(plan)),
                         'Day 21: write its day spec (plan.md: "One more day, numbered after the last.")')

    def test_a_finished_day_with_boxes_open_is_closed_not_done(self):
        days = sd.settle([a_day(1, ticked=0, total=7), a_day(2), a_day(3, kinds=["code"])], [1, 2, 3])
        self.assertEqual([d["status"] for d in days], ["closed", "done", "active"])

    def test_a_split_close_ends_the_day_only_with_its_last_part(self):
        part1 = a_day(43, ticked=1, total=27, kinds=["close"], titles=["Day 43 close, part 1: the ledger"])
        self.assertEqual(sd.settle([part1], [43])[0]["status"], "active")  # #428: boxes still open
        part2 = a_day(43, ticked=27, total=27, kinds=["close", "close"], titles=["Day 43 close, part 1", "Day 43 close, part 2"])
        self.assertEqual(sd.settle([part2], [43])[0]["status"], "done")
        whole = a_day(5, ticked=5, total=7, kinds=["close"], titles=["Day 05: tick the boxes"])
        self.assertEqual(sd.settle([whole], [5])[0]["status"], "closed")  # one close, boxes left open

    def test_the_next_step_is_the_platform_then_the_stop(self):
        days = sd.settle([a_day(16, kinds=["close"]), a_day(17)], [16, sd.PLATFORM, 17])
        lines = {sd.PLATFORM: "New day specs, numbered from 38."}
        self.assertEqual(sd.next_step(days, [], [16, sd.PLATFORM, 17], None, lines),
                         'Day 38: write its day spec (plan.md: "New day specs, numbered from 38.")')
        days = sd.settle([a_day(28, kinds=["close"]), a_day(29)], [28, 29])
        self.assertIn("stop and evaluate", sd.next_step(days, [], [28, 29], 28))

    def test_numbered_tracks_are_their_own_and_a_split_track_is_its_letter(self):
        tracks_section = """| Track | Owner | Work |
|---|---|---|
| 0 | | Work |
| A1 | | Work |
| A2 | | Work |
| B | | Work |"""
        self.assertEqual(sd.track_names(tracks_section), ["0", "A1", "A2", "B"])
        self.assertEqual(sd.merged_tracks(["day-39/track-0-x", "day-39/track-a1-key"], ["0", "A1", "A2", "B"]),
                         ["0", "A1"])
        self.assertEqual(sd.merged_tracks(["day-15/track-c1-rate", "day-15/track-c2-cors", "day-38/track-c-fix-harness"],
                                          ["0", "A", "B", "C", "D"]),
                         ["C"])
        self.assertEqual(sd.merged_tracks(["day-39/spec-written"], ["0", "A1", "A2", "B"]), [])
        # A track split again past the gate (Day 17's B1 into b1a..b1c): the letter after the digits
        # is a part of that track, not a track of its own.
        self.assertEqual(sd.merged_tracks(["day-17/track-b1a-service-key", "day-17/track-b1c-trusted-callers",
                                           "day-17/track-b2b-internal-client-and-breaker"],
                                          ["0", "A1", "A2", "B1", "B2", "C1"]),
                         ["B1", "B2"])
        # A table that names the letter (Day 20's 0a, 0b) makes it a track of its own.
        self.assertEqual(sd.track_names("| 0a | | Work |\n| 0b | | Work |\n| A | | Work |"), ["0a", "0b", "A"])
        self.assertEqual(sd.merged_tracks(["day-20/track-0a-jobs-db-seams"], ["0a", "0b", "A"]), ["0a"])

    def test_a_branch_that_names_no_day_is_read_by_its_title(self):
        # #321, Day 28's Track D, came from a branch that named no day.
        pr = dict(headRefName="claude/focused-bell-qqwqdx",
                  title="ABC-82 Day 28 track D: stopping-point review, plan changed after Phase 5")
        self.assertEqual(sd.merged_tracks([sd.day_branch(pr)], ["0", "A1", "E", "D"]), ["D"])
        # A day's own branch wins over its title, and a title that names no track changes nothing.
        own = dict(headRefName="day-28/track-e-ABC-84-account-healthcheck", title="Day 28 track D: wrong")
        self.assertEqual(sd.day_branch(own), own["headRefName"])
        other = dict(headRefName="claude/focused-sagan-96xo1w", title="account-service README: pull the image")
        self.assertEqual(sd.day_branch(other), other["headRefName"])


if __name__ == "__main__":
    unittest.main()
