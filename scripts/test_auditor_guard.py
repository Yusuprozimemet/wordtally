"""scripts/auditor-guard.py blocks an auditor's writing commands and finds what got past it. The
command tests read command text; the stop tests change a scratch repository between the auditor's
first command and its stop; the last checks that every auditor's frontmatter wires both hooks.

    python scripts/test_auditor_guard.py
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
SCRIPT = os.path.join(HERE, "auditor-guard.py")
AGENTS = os.path.join(HERE, os.pardir, ".claude", "agents")
_spec = importlib.util.spec_from_file_location("auditor_guard", SCRIPT)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

WRITES = [
    "git checkout main", 'git -C "/tmp/a replay" switch -c x', "cd /tmp/replay && git stash",
    'bash -c "git reset --hard HEAD~1"', "git branch new-branch", "git branch -D old", "git tag v1",
    "git config user.name x", "git fetch origin", "git commit -m x", "env FOO=1 git push",
    "echo hi\ngit restore README.md", "gh pr comment 45 --body hi", "gh pr merge 45",
    "gh pr checkout 3", "gh issue create -t x", "gh api -X POST repos/o/r/issues",
    "gh api repos/o/r/issues -f title=t", "gh api --method=PATCH repos/o/r",
]
READS = [
    "git log --oneline -5", "git -C /tmp/x show HEAD:plan.md", "git status --short",
    "git diff --stat main...HEAD", "git branch -a", "git branch --show-current", "git tag -l",
    "git stash list", "git worktree list", "git remote -v", "git config --get user.name",
    "git clone -q . /tmp/replay", "gh pr list --state merged --limit 400", "gh pr view 45",
    "gh auth status", "gh api repos/o/r/branches/main/protection",
    "gh api -X GET repos/o/r/pulls -f state=all", 'grep -rn "git checkout" .claude',
    "python -m unittest discover -s tests -t .", "python scripts/spec-drift.py --out /tmp/d.json",
]


class CommandTest(unittest.TestCase):
    def test_blocks_a_command_that_writes(self):
        for command in WRITES:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked(command))

    def test_lets_a_read_through(self):
        for command in READS:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked(command))

    def test_the_hook_exits_2_with_the_reason(self):
        def hook(command):
            data = {"hook_event_name": "PreToolUse", "agent_id": "t", "tool_name": "Bash",
                    "tool_input": {"command": command}}
            env = dict(os.environ, CLAUDE_PROJECT_DIR=self.repo, TMP=self.repo, TEMP=self.repo,
                       TMPDIR=self.repo)  # the snapshot lands in the scratch directory
            return subprocess.run([sys.executable, SCRIPT, "pre"], input=json.dumps(data),
                                  capture_output=True, text=True, env=env)
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo, True)
        blocked = hook("git checkout main")
        self.assertEqual((blocked.returncode, "git checkout" in blocked.stderr), (2, True))
        self.assertEqual(hook("git log -1").returncode, 0)


def _git(repo, *args):
    subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class StopTest(unittest.TestCase):
    def setUp(self):
        self.repo, self.store = tempfile.mkdtemp(), tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.addCleanup(shutil.rmtree, self.store, True)
        _git(self.repo, "init", "-q", "-b", "main")
        with open(os.path.join(self.repo, "a.txt"), "wb") as f:
            f.write(b"a\n")
        _git(self.repo, "add", "a.txt")
        _git(self.repo, "commit", "-q", "-m", "a")

    def audit(self, change, stop_hook_active=False):
        data = {"agent_id": "t", "tool_input": {"command": "git log"}}
        self.assertEqual(guard.run("pre", data, self.repo, self.store), (0, ""))
        change()
        return guard.run("stop", dict(data, stop_hook_active=stop_hook_active), self.repo, self.store)

    def write(self, name, text=b"x\n"):
        with open(os.path.join(self.repo, name), "wb") as f:
            f.write(text)

    def test_a_change_sends_the_auditor_back(self):
        cases = {
            "branch": lambda: _git(self.repo, "checkout", "-q", "-b", "other"),
            "status": lambda: self.write("a.txt"),
            "refs": lambda: _git(self.repo, "branch", "kept"),
            "stash": lambda: (self.write("a.txt"), _git(self.repo, "stash", "-q")),
            "HEAD": lambda: _git(self.repo, "commit", "-q", "--allow-empty", "-m", "b"),
        }
        for key, change in cases.items():
            with self.subTest(changed=key):
                self.setUp()
                code, message = self.audit(change)
                self.assertEqual(code, 2)
                self.assertIn(f"\n{key}: ", message)

    def test_a_scratch_file_left_behind_is_a_change(self):
        code, message = self.audit(lambda: self.write("scratch_test.py"))
        self.assertEqual((code, "?? scratch_test.py" in message), (2, True))

    def test_the_second_stop_ends_and_tells_the_main_session(self):
        self.audit(lambda: self.write("a.txt"))
        code, message = guard.run("stop", {"agent_id": "t", "stop_hook_active": True}, self.repo, self.store)
        self.assertEqual(code, 0)
        self.assertIn("a.txt", json.loads(message)["systemMessage"])
        self.assertEqual(os.listdir(self.store), [])

    def test_an_untouched_repository_stops_clean(self):
        self.assertEqual(self.audit(lambda: None), (0, ""))
        self.assertEqual(os.listdir(self.store), [])

    def test_no_command_run_no_snapshot_stops_clean(self):
        self.assertEqual(guard.run("stop", {"agent_id": "t"}, self.repo, self.store), (0, ""))


class FrontmatterTest(unittest.TestCase):
    def test_every_auditor_wires_both_hooks(self):
        auditors = 0
        for name in sorted(os.listdir(AGENTS)):
            with open(os.path.join(AGENTS, name), encoding="utf-8") as f:
                front = f.read().split("\n---", 1)[0]
            tools = re.search(r"^tools: (.*)$", front, re.M).group(1)
            if "Read-only" not in front or "Bash" not in tools:
                continue
            auditors += 1
            with self.subTest(agent=name):
                self.assertRegex(front, r'(?s)PreToolUse:.*matcher: "?Bash.*auditor-guard\.py" pre')
                self.assertRegex(front, r'(?s)Stop:.*auditor-guard\.py" stop')
        self.assertEqual(auditors, 5)


if __name__ == "__main__":
    unittest.main()
