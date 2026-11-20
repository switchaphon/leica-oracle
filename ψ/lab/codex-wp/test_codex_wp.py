"""Unit tests for codex_wp.py. Offline: no Codex call, no network. Run:

    python3 -m unittest -q test_codex_wp        (from this directory)

Every test here encodes something that went wrong, or nearly did, on 2026-11-02 / 2026-10-07:
  - review looked at the working tree, the worker had already committed -> diff must be base..HEAD
  - the worker's `git add -A` committed __pycache__ -> junk and ownership are checked per path
  - an exit code of 0 hid a dead login -> success needs turn.completed in the event log
  - the quota is a weekly window with no credits -> pace the burst, hard stop near the cap
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codex_wp as cw  # noqa: E402

# No test may reach the real Codex. On 2026-11-20 a slot-wait test raced under load, slipped past the wait and
# dispatched a real worker on gpt-5.6-sol (168k tokens in). A test that wants a worker sets its own fake; any other
# path to a worker now fails loudly instead of spending quota.
os.environ["CODEX_WP_BIN"] = str(Path(tempfile.gettempdir(), "codex-wp-tests-never-call-the-real-codex"))

WP_TEXT = """## WP-1: implement add()
- Goal: make test_add.py pass.
- Files owned: add.py, `src/lib/**`
- Context: none
- Verify with: python3 -m unittest -q test_add
- Report back: files changed
"""


class ParseWP(unittest.TestCase):
    def test_title_owned_verify(self):
        wp = cw.parse_wp(WP_TEXT)
        self.assertEqual(wp.title, "implement add()")
        self.assertEqual(wp.owned, ["add.py", "src/lib/**"])
        self.assertEqual(wp.verify, ["python3 -m unittest -q test_add"])

    def test_bullet_list_form(self):
        text = "## WP-2: x\n- Files owned:\n  - a.py\n  - b/**\n- Verify with:\n  - `pytest -q`\n  - ruff check .\n"
        wp = cw.parse_wp(text)
        self.assertEqual(wp.owned, ["a.py", "b/**"])
        self.assertEqual(wp.verify, ["pytest -q", "ruff check ."])

    def test_bold_keys(self):
        wp = cw.parse_wp("# T\n- **Files owned**: x.py\n")
        self.assertEqual(wp.title, "T")
        self.assertEqual(wp.owned, ["x.py"])

    def test_verify_keeps_commas(self):
        wp = cw.parse_wp("## WP-3: y\n- Files owned: y.py\n- Verify with: pytest -k 'a or b' -q, --maxfail=1\n")
        self.assertEqual(wp.verify, ["pytest -k 'a or b' -q, --maxfail=1"])

    def test_missing_owned_refuses(self):
        with self.assertRaises(cw.WPError):
            cw.parse_wp("## WP-4: z\n- Goal: something\n")

    def test_note_glued_to_a_path_is_refused_not_absorbed(self):
        """maw-codex-team-kit kept '# comment' inside charter values and then killed the wrong window,
        silently. Here a note glued to a path would become part of the path and fail every ownership check."""
        for line in ("add.py   # new file", "add.py (new file)", "a.py, b.py  # both new"):
            with self.assertRaises(cw.WPError, msg=line):
                cw.parse_wp(f"## WP-5: n\n- Files owned: {line}\n")

    def test_ordinary_paths_still_pass(self):
        wp = cw.parse_wp("## WP-6: n\n- Files owned: src/my-file.test.ts, app/[id]/page.tsx, docs/\n")
        self.assertEqual(wp.owned, ["src/my-file.test.ts", "app/[id]/page.tsx", "docs/"])

    def test_ignore_lists_the_generated_paths_the_lead_expects(self):
        wp = cw.parse_wp("## WP-7: n\n- Files owned: a.ts\n- Ignore: dist-test/, coverage/\n")
        self.assertEqual(wp.ignore, ["dist-test/", "coverage/"])
        self.assertEqual(cw.parse_wp(WP_TEXT).ignore, [])

    def test_a_note_glued_to_an_ignore_path_is_refused_too(self):
        with self.assertRaises(cw.WPError):
            cw.parse_wp("## WP-8: n\n- Files owned: a.ts\n- Ignore: dist-test/ (made by pnpm test)\n")


class Owned(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(cw.match_owned("add.py", ["add.py"]))

    def test_double_star(self):
        self.assertTrue(cw.match_owned("src/a/b.py", ["src/**"]))

    def test_single_star_does_not_cross_directories(self):
        self.assertFalse(cw.match_owned("src/a/b.py", ["src/*"]))
        self.assertTrue(cw.match_owned("src/b.py", ["src/*"]))

    def test_trailing_slash_means_the_tree(self):
        self.assertTrue(cw.match_owned("docs/x/y.md", ["docs/"]))

    def test_not_owned(self):
        self.assertFalse(cw.match_owned("__pycache__/add.cpython-314.pyc", ["add.py"]))
        self.assertFalse(cw.match_owned("add.py.bak", ["add.py"]))

    def test_globstar_prefix(self):
        self.assertTrue(cw.match_owned("a/b/c.ts", ["**/c.ts"]))
        self.assertTrue(cw.match_owned("c.ts", ["**/c.ts"]))

    def test_leading_dot_slash(self):
        self.assertTrue(cw.match_owned("./add.py", ["add.py"]))

    def test_dotfile_not_mangled(self):
        self.assertTrue(cw.match_owned(".eslintrc", [".eslintrc"]))


class Junk(unittest.TestCase):
    def test_junk(self):
        for p in ["__pycache__/a.cpython-314.pyc", "x/__pycache__/y.pyc", "node_modules/a/b.js",
                  ".DS_Store", "build.log", ".env", ".env.local", ".omx/state/x.json", "a/b/c.pyc"]:
            self.assertTrue(cw.is_junk(p), p)

    def test_not_junk(self):
        for p in ["add.py", ".env.example", "src/app.ts", "docs/readme.md", ".gitignore"]:
            self.assertFalse(cw.is_junk(p), p)


class Assess(unittest.TestCase):
    def test_flags_violation_and_committed_junk(self):
        a = cw.assess_changes(committed=["add.py", "__pycache__/a.pyc"], dirty=["extra.txt"], owned=["add.py"])
        self.assertEqual(a.owned_changed, ["add.py"])
        self.assertEqual(a.violations, ["extra.txt"])
        self.assertEqual(a.committed_junk, ["__pycache__/a.pyc"])
        self.assertFalse(a.clean)

    def test_untracked_junk_is_only_a_warning(self):
        a = cw.assess_changes(committed=["add.py"], dirty=["__pycache__/a.pyc"], owned=["add.py"])
        self.assertTrue(a.clean)
        self.assertEqual(a.dirty_junk, ["__pycache__/a.pyc"])

    def test_nothing_changed_is_not_clean(self):
        self.assertFalse(cw.assess_changes([], [], ["add.py"]).clean)

    def test_junk_wins_even_when_owned_by_glob(self):
        a = cw.assess_changes(committed=["__pycache__/a.pyc"], dirty=[], owned=["**"])
        self.assertEqual(a.committed_junk, ["__pycache__/a.pyc"])
        self.assertEqual(a.owned_changed, [])


class AssessIgnore(unittest.TestCase):
    """pops-655, 2026-11-02: the repo's own `pnpm test` leaves dist-test/ behind. The worker could not delete it (the
    sandbox rejects recursive rm), so it hid it in /tmp to satisfy rule 6. The lead declares such paths up front instead."""

    def test_declared_generated_paths_are_a_warning_not_a_violation(self):
        a = cw.assess_changes(committed=["add.py"], dirty=["dist-test/test/x.js"], owned=["add.py"],
                              ignore=["dist-test/"])
        self.assertTrue(a.clean)
        self.assertEqual(a.dirty_junk, ["dist-test/test/x.js"])

    def test_without_the_declaration_they_are_a_violation(self):
        a = cw.assess_changes(committed=["add.py"], dirty=["dist-test/test/x.js"], owned=["add.py"])
        self.assertEqual(a.violations, ["dist-test/test/x.js"])

    def test_a_declared_path_that_was_committed_is_still_flagged(self):
        a = cw.assess_changes(committed=["add.py", "dist-test/x.js"], dirty=[], owned=["add.py"], ignore=["dist-test/"])
        self.assertEqual(a.committed_junk, ["dist-test/x.js"])
        self.assertFalse(a.clean)


class CommitIgnore(unittest.TestCase):
    def test_declared_paths_are_never_committed_even_when_a_glob_owns_them(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/i1", wt)
            (wt / "src").mkdir()
            (wt / "src" / "a.ts").write_text("export const a = 1\n")
            (wt / "dist-test").mkdir()
            (wt / "dist-test" / "x.js").write_text("y")
            self.assertTrue(cw.commit_owned(wt, ["**"], "wp: t", ignore=["dist-test/"]))
            self.assertEqual(cw.committed_paths(wt, base), ["src/a.ts"])
            self.assertEqual(cw.dirty_paths(wt), ["dist-test/x.js"])


class Decide(unittest.TestCase):
    CLEAN = cw.Assessment(["add.py"], [], [], [])

    def test_pass(self):
        self.assertEqual(cw.decide([], self.CLEAN), ("PASS", []))

    def test_worker_failure_beats_everything(self):
        status, why = cw.decide(["no turn.completed in the event log"], self.CLEAN)
        self.assertEqual(status, "FAIL")
        self.assertIn("turn.completed", why[0])

    def test_revise_on_violation(self):
        status, why = cw.decide([], cw.Assessment(["add.py"], ["extra.txt"], [], []))
        self.assertEqual(status, "REVISE")
        self.assertIn("extra.txt", why[0])

    def test_revise_when_nothing_owned_changed(self):
        self.assertEqual(cw.decide([], cw.Assessment([], [], [], []))[0], "REVISE")


class Porcelain(unittest.TestCase):
    def test_parse(self):
        out = " M add.py\0?? extra.txt\0R  new.py\0old.py\0A  sub/dir/f.py\0"
        self.assertEqual(cw.parse_porcelain_z(out), ["add.py", "extra.txt", "new.py", "sub/dir/f.py"])

    def test_empty(self):
        self.assertEqual(cw.parse_porcelain_z(""), [])


def rl(used, elapsed, window_minutes=10080, reached=None, now=1_000_000.0, secondary=None):
    span = window_minutes * 60
    primary = {"used_percent": used, "window_minutes": window_minutes,
               "resets_at": now + (1 - elapsed) * span}
    return ({"primary": primary, "secondary": secondary, "rate_limit_reached_type": reached,
             "credits": {"has_credits": False}}, now)


class Pace(unittest.TestCase):
    def verdict(self, used, elapsed, **kw):
        r, now = rl(used, elapsed, **kw)
        return cw.pace_verdict(r, now)

    def test_fresh_window_small_use_is_go(self):
        self.assertEqual(self.verdict(0.0, 0.003).kind, "GO")

    def test_fresh_window_burst_is_hold(self):
        v = self.verdict(12.0, 0.003)
        self.assertEqual(v.kind, "HOLD")
        self.assertAlmostEqual(v.allowed, 10.3, places=1)

    def test_ahead_of_pace_but_inside_the_slack(self):
        self.assertEqual(self.verdict(29.0, 0.20).kind, "GO")  # allowed = 20 + 10

    def test_cap_beats_pace_late_in_the_window(self):
        v = self.verdict(86.0, 0.95)
        self.assertEqual(v.kind, "HOLD")
        self.assertEqual(v.allowed, 85.0)

    def test_hard_stop_is_fallback(self):
        self.assertEqual(self.verdict(91.0, 0.95).kind, "FALLBACK")

    def test_limit_reached_is_fallback(self):
        r, now = rl(10.0, 0.5, reached="primary")
        self.assertEqual(cw.pace_verdict(r, now).kind, "FALLBACK")

    def test_rolled_over_window_is_go(self):
        r, now = rl(95.0, 1.0)
        r["primary"]["resets_at"] = now - 5
        self.assertEqual(cw.pace_verdict(r, now).kind, "GO")

    def test_short_window_is_not_paced(self):
        self.assertEqual(self.verdict(50.0, 0.10, window_minutes=300).kind, "GO")

    def test_no_snapshot_is_unknown(self):
        self.assertEqual(cw.pace_verdict(None, 0).kind, "UNKNOWN")

    def test_worst_window_wins(self):
        sec = {"used_percent": 95.0, "window_minutes": 10080, "resets_at": 1_000_000.0 + 3 * 86400}
        r, now = rl(5.0, 0.5, window_minutes=300, secondary=sec)
        self.assertEqual(cw.pace_verdict(r, now).kind, "FALLBACK")


class Events(unittest.TestCase):
    @staticmethod
    def lines(*objs):
        return "\n".join(json.dumps(o) for o in objs)

    def test_completed(self):
        s = cw.summarize_events(self.lines(
            {"type": "thread.started", "thread_id": "t-1"}, {"type": "turn.started"},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}}))
        self.assertTrue(s.completed)
        self.assertFalse(s.failed)
        self.assertEqual(s.thread_id, "t-1")
        self.assertEqual(s.usage["input_tokens"], 10)

    def test_missing_turn_completed_is_not_success(self):
        s = cw.summarize_events(self.lines({"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"}))
        self.assertFalse(s.completed)

    def test_turn_failed(self):
        s = cw.summarize_events(self.lines({"type": "turn.failed", "error": {"message": "401 Missing bearer"}}))
        self.assertTrue(s.failed)
        self.assertIn("401", s.errors[0])

    def test_error_event_alone_does_not_fail_a_completed_turn(self):
        s = cw.summarize_events(self.lines({"type": "error", "message": "Reconnecting 1/5"},
                                           {"type": "turn.completed", "usage": {}}))
        self.assertTrue(s.completed)
        self.assertFalse(s.failed)
        self.assertEqual(s.errors, ["Reconnecting 1/5"])

    def test_garbage_lines_ignored(self):
        s = cw.summarize_events("not json\n" + json.dumps({"type": "turn.completed", "usage": {}}))
        self.assertTrue(s.completed)


def rollout_line(ts, used, window=10080, resets=2_000_000_000):
    return json.dumps({"timestamp": ts, "type": "event_msg", "payload": {
        "type": "token_count", "info": None,
        "rate_limits": {"primary": {"used_percent": used, "window_minutes": window, "resets_at": resets},
                        "secondary": None, "plan_type": "test-plan"}}})


class Rollouts(unittest.TestCase):
    def test_last_token_count_wins(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "rollout-x.jsonl"
            f.write_text("\n".join([
                json.dumps({"timestamp": "2026-11-02T08:00:00.000Z", "type": "session_meta", "payload": {}}),
                rollout_line("2026-11-02T08:01:00.000Z", 1.0),
                rollout_line("2026-11-02T08:02:00.000Z", 2.5)]) + "\n")
            ts, limits = cw.rate_limits_from_rollout(f)
            self.assertEqual(limits["primary"]["used_percent"], 2.5)
            self.assertEqual(ts, "2026-11-02T08:02:00.000Z")

    def test_tail_read_still_finds_the_last_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "rollout-big.jsonl"
            filler = json.dumps({"type": "response_item", "payload": {"text": "x" * 500}})
            f.write_text("\n".join([filler] * 50 + [rollout_line("2026-11-02T08:09:00.000Z", 4.0)]) + "\n")
            _, limits = cw.rate_limits_from_rollout(f, tail_bytes=2000)
            self.assertEqual(limits["primary"]["used_percent"], 4.0)

    def test_no_token_count_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "rollout-none.jsonl"
            f.write_text(json.dumps({"type": "session_meta", "payload": {}}) + "\n")
            self.assertIsNone(cw.rate_limits_from_rollout(f))

    def test_latest_snapshot_uses_the_newest_file_across_homes(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d, "a/sessions/2026/11/02")
            b = Path(d, "b/sessions/2026/11/02")
            a.mkdir(parents=True)
            b.mkdir(parents=True)
            fa = a / "rollout-2026-11-02T01-00-00-aaa.jsonl"
            fb = b / "rollout-2026-11-02T02-00-00-bbb.jsonl"
            fa.write_text(rollout_line("2026-11-02T01:00:00.000Z", 1.0) + "\n")
            fb.write_text(rollout_line("2026-11-02T02:00:00.000Z", 7.0) + "\n")
            os.utime(fa, (1000, 1000))
            os.utime(fb, (2000, 2000))
            snap = cw.latest_snapshot([Path(d, "a"), Path(d, "b")])
            self.assertEqual(snap.rate_limits["primary"]["used_percent"], 7.0)

    def test_no_rollouts_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(cw.latest_snapshot([Path(d)]))

    def test_find_rollout_by_thread_id(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "sessions/2026/11/02")
            p.mkdir(parents=True)
            f = p / "rollout-2026-11-02T15-17-40-01a19b55-e6b2.jsonl"
            f.write_text("{}\n")
            self.assertEqual(cw.find_rollout_for_thread([Path(d)], "01a19b55-e6b2"), f)
            self.assertIsNone(cw.find_rollout_for_thread([Path(d)], "nope"))
            self.assertIsNone(cw.find_rollout_for_thread([Path(d)], None))


class Argv(unittest.TestCase):
    def build(self, **kw):
        base = dict(codex_bin="codex", worktree=Path("/w"), model="gpt-5.6-sol",
                    sandbox="workspace-write", report_path=Path("/r.md"))
        base.update(kw)
        return cw.build_exec_argv(**base)

    def test_workspace_write_shape(self):
        a = self.build()
        self.assertEqual(a[:2], ["codex", "exec"])
        self.assertIn("--json", a)
        self.assertIn("--ignore-user-config", a)
        self.assertEqual(a[a.index("-s") + 1], "workspace-write")
        self.assertEqual(a[a.index("-m") + 1], "gpt-5.6-sol")
        self.assertEqual(a[a.index("-C") + 1], "/w")
        self.assertEqual(a[a.index("-o") + 1], "/r.md")
        self.assertEqual(a[-1], "-")  # the prompt arrives on stdin

    def test_never_bypasses_the_sandbox(self):
        a = self.build()
        for bad in ("--dangerously-bypass-approvals-and-sandbox", "--yolo", "--madmax", "--full-auto"):
            self.assertNotIn(bad, a)

    def test_rejects_full_access(self):
        with self.assertRaises(ValueError):
            self.build(sandbox="danger-full-access")

    def test_effort_override(self):
        self.assertIn('model_reasoning_effort="medium"', self.build(effort="medium"))

    def test_skip_git_check_only_when_asked(self):
        self.assertNotIn("--skip-git-repo-check", self.build())
        self.assertIn("--skip-git-repo-check", self.build(skip_git_check=True))

    def test_worker_environment_is_narrowed(self):
        """DATABASE_URL-style variables carry passwords but no KEY/TOKEN in the name."""
        a = self.build()
        i = a.index("shell_environment_policy.inherit=core")
        self.assertEqual(a[i - 1], "-c")


class Prompt(unittest.TestCase):
    def test_preamble_carries_the_rules_learned_on_2026_11_02(self):
        p = cw.compose_prompt(WP_TEXT)
        for needle in ("Files owned", "Do NOT commit", "git add -A", "No network",
                       "Never hide or work around a failure", "AGENTS.md"):
            self.assertIn(needle, p)
        self.assertTrue(p.endswith(WP_TEXT))

    def test_preamble_does_not_push_the_worker_to_hide_files_it_cannot_delete(self):
        """2026-11-02: rule 6 said 'leave nothing behind'. The sandbox rejected rm -rf, so the worker moved dist-test to /tmp."""
        p = cw.compose_prompt(WP_TEXT)
        self.assertIn("Never move, rename or hide", p)
        self.assertNotIn("Leave no generated files behind", p)


class Slots(unittest.TestCase):
    def test_limit_and_release(self):
        with tempfile.TemporaryDirectory() as d:
            held = [cw.acquire_slot(Path(d), 3) for _ in range(3)]
            self.assertEqual(sorted(s for _, s in held), [1, 2, 3])
            with self.assertRaises(cw.SlotBusy):
                cw.acquire_slot(Path(d), 3)
            os.close(held[0][0])
            fd, slot = cw.acquire_slot(Path(d), 3)
            self.assertEqual(slot, held[0][1])
            for f, _ in held[1:]:
                os.close(f)
            os.close(fd)


def sh(cwd, *args):
    return subprocess.run(args, cwd=str(cwd), check=True, capture_output=True, text=True).stdout.strip()


def make_repo(d):
    repo = Path(d, "base")
    repo.mkdir()
    sh(repo, "git", "init", "-q", "-b", "main")
    sh(repo, "git", "config", "user.email", "t@example.invalid")
    sh(repo, "git", "config", "user.name", "t")
    (repo / "add.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    (repo / "test_add.py").write_text("import unittest\nfrom add import add\n\n\nclass T(unittest.TestCase):\n"
                                      "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "base")
    return repo


class GitFlow(unittest.TestCase):
    def test_review_must_diff_against_base_not_the_working_tree(self):
        """2026-11-02: the worker committed, plain `git diff` was empty. base..HEAD shows the work."""
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/t0", wt)
            (wt / "add.py").write_text("def add(a, b):\n    return a + b\n")
            (wt / "__pycache__").mkdir()
            (wt / "__pycache__" / "a.pyc").write_bytes(b"\0")
            sh(wt, "git", "add", "-A")
            sh(wt, "git", "commit", "-q", "-m", "worker commit")
            self.assertEqual(sh(wt, "git", "diff"), "")  # what the first review looked at
            self.assertEqual(cw.dirty_paths(wt), [])
            committed = cw.committed_paths(wt, base)
            self.assertCountEqual(committed, ["add.py", "__pycache__/a.pyc"])
            a = cw.assess_changes(committed, cw.dirty_paths(wt), ["add.py"])
            self.assertEqual(a.committed_junk, ["__pycache__/a.pyc"])
            self.assertEqual(cw.decide([], a)[0], "REVISE")

    def test_worktree_commit_only_owned_files(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/t1", wt)
            self.assertEqual(base, sh(repo, "git", "rev-parse", "HEAD"))
            (wt / "add.py").write_text("def add(a, b):\n    return a + b\n")
            (wt / "extra.txt").write_text("x")
            (wt / "__pycache__").mkdir()
            (wt / "__pycache__" / "a.pyc").write_bytes(b"\0")
            self.assertCountEqual(cw.dirty_paths(wt), ["add.py", "extra.txt", "__pycache__/a.pyc"])
            sha = cw.commit_owned(wt, ["add.py"], "wp: implement add()")
            self.assertTrue(sha)
            self.assertEqual(cw.committed_paths(wt, base), ["add.py"])
            self.assertCountEqual(cw.dirty_paths(wt), ["extra.txt", "__pycache__/a.pyc"])
            a = cw.assess_changes(cw.committed_paths(wt, base), cw.dirty_paths(wt), ["add.py"])
            self.assertEqual(a.violations, ["extra.txt"])
            self.assertEqual(a.dirty_junk, ["__pycache__/a.pyc"])

    def test_prestaged_non_owned_stays_out_of_the_commit(self):
        """A worker that ignored 'do not git add' must not smuggle files into the lead's commit."""
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/t5", wt)
            (wt / "add.py").write_text("def add(a, b):\n    return a + b\n")
            (wt / "extra.txt").write_text("x")
            sh(wt, "git", "add", "extra.txt")
            self.assertTrue(cw.commit_owned(wt, ["add.py"], "wp: only add.py"))
            self.assertEqual(cw.committed_paths(wt, base), ["add.py"])
            self.assertIn("extra.txt", cw.dirty_paths(wt))

    def test_bracketed_next_js_paths_are_literal(self):
        """app/[id]/page.tsx: without literal pathspecs git reads [id] as a character class."""
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/t6", wt)
            (wt / "app" / "[id]").mkdir(parents=True)
            (wt / "app" / "[id]" / "page.tsx").write_text("export default 1\n")
            self.assertTrue(cw.commit_owned(wt, ["app/[id]/**"], "wp: dynamic route"))
            self.assertEqual(cw.committed_paths(wt, base), ["app/[id]/page.tsx"])

    def test_commit_owned_with_nothing_to_commit(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            cw.make_worktree(repo, "HEAD", "wp/t2", wt)
            (wt / "extra.txt").write_text("x")
            self.assertIsNone(cw.commit_owned(wt, ["add.py"], "wp: nothing"))

    def test_deleted_owned_file_counts_as_a_change(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            wt = Path(d, "wt")
            base = cw.make_worktree(repo, "HEAD", "wp/t3", wt)
            (wt / "add.py").unlink()
            self.assertTrue(cw.commit_owned(wt, ["add.py"], "wp: remove add.py"))
            self.assertEqual(cw.committed_paths(wt, base), ["add.py"])

    def test_bad_base_ref_raises(self):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            with self.assertRaises(cw.GitError):
                cw.make_worktree(repo, "no-such-ref", "wp/t4", Path(d, "wt"))


class Commands(unittest.TestCase):
    def test_run_commands_reports_exit_codes_and_tails(self):
        with tempfile.TemporaryDirectory() as d:
            res = cw.run_commands(["true", "echo boom >&2; exit 3"], Path(d), timeout=20)
            self.assertEqual([r[1] for r in res], [0, 3])
            self.assertIn("boom", res[1][2])


class SelftestRecord(unittest.TestCase):
    """2026-11-02 16:36: someone upgraded the Codex CLI from 0.144.1 to 0.166.0, silently, 50 minutes after the only
    selftest. A pass proves only the version it ran on, so `check` must say when that version (or the model) changed."""
    REC = {"codex_version": "codex-cli 0.166.0", "model": "gpt-5.6-sol", "ts": 1_000_000.0, "result": "PASS"}

    def status(self, rec, version="codex-cli 0.166.0", model="gpt-5.6-sol", later=3600.0):
        return cw.selftest_status(rec, version, model, 1_000_000.0 + later)

    def test_same_version_is_ok(self):
        kind, text = self.status(self.REC)
        self.assertEqual(kind, "OK")
        self.assertIn("0.166.0", text)

    def test_no_record(self):
        self.assertEqual(self.status(None)[0], "NONE")

    def test_an_upgrade_is_visible(self):
        kind, text = self.status(self.REC, version="codex-cli 0.170.0")
        self.assertEqual(kind, "DIFFERENT")
        self.assertIn("0.166.0", text)
        self.assertIn("0.170.0", text)

    def test_a_model_change_is_visible(self):
        self.assertEqual(self.status(self.REC, model="gpt-6.1-sol")[0], "DIFFERENT")

    def test_a_failed_selftest_is_not_a_pass(self):
        self.assertEqual(self.status(dict(self.REC, result="FAIL"))[0], "FAILED")

    def test_an_old_pass_is_stale(self):
        self.assertEqual(self.status(self.REC, later=4 * 86400.0)[0], "STALE")

    def test_record_round_trip_and_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "selftest.json")
            self.assertIsNone(cw.read_selftest_record(p))      # missing file
            cw.write_selftest_record(p, self.REC)
            self.assertEqual(cw.read_selftest_record(p), self.REC)
            p.write_text("{not json")
            self.assertIsNone(cw.read_selftest_record(p))      # a corrupt record reads as no record


class FormatEvent(unittest.TestCase):
    """`follow` is for a human watching a tmux pane: commands, edits, what the agent says, and nothing else."""

    @staticmethod
    def cmd_started(command):
        return {"type": "item.started", "item": {"type": "command_execution", "command": command, "status": "in_progress"}}

    def test_command_started_strips_the_shell_wrapper(self):
        self.assertEqual(cw.format_event(self.cmd_started('/bin/zsh -lc "pwd && ls -la"')), ["$ pwd && ls -la"])

    def test_long_commands_are_truncated(self):
        line = cw.format_event(self.cmd_started("echo " + "x" * 400))[0]
        self.assertLessEqual(len(line), 150)
        self.assertTrue(line.endswith("..."))

    def test_command_completed_shows_the_exit_code(self):
        ok = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0, "aggregated_output": "fine\n"}}
        self.assertEqual(cw.format_event(ok), ["  exit 0"])

    def test_failed_command_shows_the_last_output_line(self):
        bad = {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 2,
                                                  "aggregated_output": "a\nb\nboom: no such file\n"}}
        self.assertEqual(cw.format_event(bad), ["  exit 2: boom: no such file"])

    def test_agent_message_is_collapsed_and_cut(self):
        o = {"type": "item.completed", "item": {"type": "agent_message", "text": "I will\n  do   it. " + "y" * 500}}
        line = cw.format_event(o)[0]
        self.assertTrue(line.startswith("agent: I will do it."))
        self.assertLessEqual(len(line), 320)

    def test_file_changes_list_paths_relative_to_the_worktree(self):
        o = {"type": "item.completed", "item": {"type": "file_change", "changes": [
            {"path": "/wt/src/a.ts", "kind": "update"}, {"path": "/wt/b.ts", "kind": "add"}]}}
        self.assertEqual(cw.format_event(o, strip="/wt/"), ["edit update src/a.ts", "edit add b.ts"])

    def test_a_file_change_is_shown_once_not_on_start_and_completion(self):
        o = {"type": "item.started", "item": {"type": "file_change", "changes": [{"path": "a", "kind": "update"}]}}
        self.assertEqual(cw.format_event(o), [])

    def test_turn_completed_shows_usage(self):
        o = {"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 800, "output_tokens": 50}}
        self.assertEqual(cw.format_event(o), ["turn completed: tokens in 1000 (cached 800) out 50"])

    def test_failure_is_shown(self):
        self.assertEqual(cw.format_event({"type": "turn.failed", "error": {"message": "401 Missing bearer"}}),
                         ["ERROR: 401 Missing bearer"])

    def test_noise_is_skipped(self):
        for o in ({"type": "turn.started"}, {"type": "thread.started", "thread_id": "x"},
                  {"type": "item.started", "item": {"type": "agent_message"}}, {"nonsense": 1}):
            self.assertEqual(cw.format_event(o), [])


class FollowTail(unittest.TestCase):
    def test_yields_lines_as_they_arrive_and_never_a_half_written_one(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "events.jsonl")
            finished = threading.Event()

            def writer():
                with open(p, "a") as f:
                    f.write(json.dumps({"n": 1}) + "\n")
                    f.flush()
                    time.sleep(0.15)
                    f.write('{"n": 2')              # half a line: must not be yielded yet
                    f.flush()
                    time.sleep(0.15)
                    f.write("}\n" + json.dumps({"n": 3}) + "\n")
                    f.flush()
                    time.sleep(0.1)
                finished.set()

            t = threading.Thread(target=writer)
            t.start()
            got = [json.loads(x) for x in cw.follow_lines(p, finished.is_set, poll=0.03)]
            t.join()
            self.assertEqual([g["n"] for g in got], [1, 2, 3])

    def test_data_written_just_before_the_run_finishes_is_not_lost(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "events.jsonl")
            p.write_text(json.dumps({"n": 1}) + "\n" + json.dumps({"n": 2}) + "\n")
            self.assertEqual(len(list(cw.follow_lines(p, lambda: True, poll=0.01))), 2)

    def test_a_file_that_never_appears_ends_when_finished(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(list(cw.follow_lines(Path(d, "nope.jsonl"), lambda: True, poll=0.01)), [])


class PrintLive(unittest.TestCase):
    """The same printer serves `follow` and `run --follow`, where it runs in a thread beside the worker."""

    def test_prints_timestamped_human_lines_and_skips_noise(self):
        import io
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "events.jsonl")
            p.write_text("\n".join(json.dumps(o) for o in [
                {"type": "thread.started", "thread_id": "t"},
                {"type": "item.started", "item": {"type": "command_execution", "command": '/bin/zsh -lc "pnpm test"'}},
                {"type": "item.completed", "item": {"type": "command_execution", "exit_code": 0}},
                {"type": "turn.completed", "usage": {"input_tokens": 5, "cached_input_tokens": 4, "output_tokens": 1}},
            ]) + "\nnot json\n")
            out = io.StringIO()
            cw.print_live(p, lambda: True, out=out, poll=0.01)
            lines = out.getvalue().splitlines()
            self.assertEqual(len(lines), 3)
            self.assertTrue(all(ln[2] == ":" for ln in lines))  # HH:MM:SS prefix
            self.assertIn("$ pnpm test", lines[0])
            self.assertIn("exit 0", lines[1])
            self.assertIn("turn completed", lines[2])

    def test_can_run_in_a_thread_next_to_a_worker(self):
        import io
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "events.jsonl")
            p.write_text("")
            out = io.StringIO()
            done = threading.Event()
            t = threading.Thread(target=cw.print_live, args=(p, done.is_set), kwargs={"out": out, "poll": 0.01})
            t.start()
            with open(p, "a") as f:
                f.write(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "hello"}}) + "\n")
            time.sleep(0.1)
            done.set()
            t.join(timeout=3)
            self.assertFalse(t.is_alive())
            self.assertIn("agent: hello", out.getvalue())


class DoneTolerance(unittest.TestCase):
    """pops-658, 2026-11-02: `done` refused a worktree whose only untracked content was the node_modules symlink its own
    --setup had created. Links and junk are not work; a real untracked file is."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.old_state = cw.STATE_DIR
        cw.STATE_DIR = Path(self.d, "state")
        self.repo = make_repo(self.d)
        self.wt = Path(self.d, "wt")
        cw.make_worktree(self.repo, "HEAD", "wp/d1", self.wt)
        self.target = Path(self.d, "shared_node_modules")
        self.target.mkdir()
        run = cw.STATE_DIR / "runs" / "r1"
        run.mkdir(parents=True)
        (run / "meta.json").write_text(json.dumps(
            {"run_id": "r1", "worktree": str(self.wt), "repo": str(self.repo), "branch": "wp/d1"}))

    def tearDown(self):
        cw.STATE_DIR = self.old_state
        self.tmp.cleanup()

    def test_links_and_junk_only(self):
        os.symlink(self.target, self.wt / "node_modules")
        (self.wt / "__pycache__").mkdir()
        (self.wt / "__pycache__" / "a.pyc").write_bytes(b"\0")
        self.assertTrue(cw.only_links_and_junk(self.wt))

    def test_a_real_untracked_file_is_not_junk(self):
        os.symlink(self.target, self.wt / "node_modules")
        (self.wt / "notes.txt").write_text("keep me")
        self.assertFalse(cw.only_links_and_junk(self.wt))

    def test_done_removes_it_keeps_the_branch_and_never_touches_the_link_target(self):
        os.symlink(self.target, self.wt / "node_modules")
        (self.target / "pkg").write_text("x")
        self.assertEqual(cw.cmd_done(argparse.Namespace(run="r1", force=False)), cw.EXIT_PASS)
        self.assertFalse(self.wt.exists())
        self.assertTrue((self.target / "pkg").exists())
        self.assertIn("wp/d1", sh(self.repo, "git", "branch", "--list", "wp/d1"))

    def test_declared_generated_paths_do_not_block_done(self):
        (self.wt / "dist-test").mkdir()
        (self.wt / "dist-test" / "x.js").write_text("y")
        self.assertFalse(cw.only_links_and_junk(self.wt))
        self.assertTrue(cw.only_links_and_junk(self.wt, extra=["dist-test/"]))

    def test_done_still_refuses_real_work(self):
        (self.wt / "notes.txt").write_text("keep me")
        self.assertEqual(cw.cmd_done(argparse.Namespace(run="r1", force=False)), cw.EXIT_REVISE)
        self.assertTrue((self.wt / "notes.txt").exists())


class BaseCheck(unittest.TestCase):
    """pops-658, 2026-11-02: --tdd ran `Verify with:` in a fresh worktree WITHOUT --setup, so a verify command that needs
    node_modules failed for the wrong reason and the red was fake."""

    def check(self, verify, setup=None):
        with tempfile.TemporaryDirectory() as d:
            repo = make_repo(d)
            old = cw.STATE_DIR
            cw.STATE_DIR = Path(d, "state")
            try:
                return cw.base_check(repo, "HEAD", verify, "rid", setup=setup)
            finally:
                cw.STATE_DIR = old

    def test_a_red_says_why_it_is_red(self):
        ok, detail = self.check(["echo 'missing feature' >&2; exit 1"])
        self.assertTrue(ok)
        self.assertIn("missing feature", detail)

    def test_already_green_is_refused(self):
        ok, detail = self.check(["true"])
        self.assertFalse(ok)
        self.assertIn("already PASSES", detail)

    def test_setup_runs_in_the_base_worktree_before_verify(self):
        ok, _ = self.check(["test -f ready.flag"], setup="touch ready.flag")
        self.assertFalse(ok)  # with the setup the worker gets, this verify passes on base, so it proves nothing

    def test_a_failing_setup_makes_the_red_untrustworthy(self):
        ok, detail = self.check(["false"], setup="exit 3")
        self.assertFalse(ok)
        self.assertIn("setup failed", detail)


# --------------------------------------------------------------------------- 0.1.4
# A: a secret preflight before the worker starts. B: a PASS that says what it checked. C: run --wait.
# Why B: run 20261103-151816 was PASS while the worker's own test run was red (1 of 71); only report.md said so.
# Why A: nothing scanned what a worker is shown; on 2026-11-19 the run records held 0 real secrets, by luck.
# Why C: one pops-pet window wrote its own retry loop after 10 BUSY exits (exit 11 never waits).

# Fixture URLs below carry `# gitleaks:allow`: every credential in them is made up, and without the marker the repo's
# oracle-service-uri-credentials rule (and codex-wp's own preflight on this repo) would block on its own tests.
SECRET = "S3cr3tPw0rd9"  # made up, never a real credential
GH_TOKEN = "ghp_" + "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kLm"  # made up, correctly shaped; split so no scanner sees it here


def write_exec(path, body):
    path = Path(path)
    path.write_text(body)
    path.chmod(0o755)
    return path


def fake_gitleaks(d, exit_code=0, findings=None, raw=None, sleep=0):
    """Stands in for gitleaks: logs cwd and argv, optionally sleeps, writes a report where --report-path says (JSON of
    `findings`, or `raw` text as is), then exits as told."""
    log = Path(d, "gitleaks-calls.log")
    report = raw if raw is not None else json.dumps(findings or [])
    script = write_exec(Path(d, f"fake-gitleaks-{exit_code}-{sleep}"), f"""#!/usr/bin/env python3
import json, os, sys, time
with open({str(log)!r}, "a") as fh:
    fh.write(json.dumps({{"cwd": os.getcwd(), "argv": sys.argv[1:]}}) + "\\n")
time.sleep({sleep})
args = sys.argv[1:]
if "--report-path" in args:
    with open(args[args.index("--report-path") + 1], "w") as fh:
        fh.write({report!r})
sys.exit({exit_code})
""")
    return script, log


def fake_codex(d, report_text, mark):
    """Stands in for `codex exec`: edits add.py in the worktree (-C), prints a minimal event stream, writes the final
    report where -o says, and leaves a mark so a test can tell whether the worker was started at all."""
    return write_exec(Path(d, "fake-codex"), f"""#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
wt = args[args.index("-C") + 1]
out = args[args.index("-o") + 1]
sys.stdin.read()
open({str(mark)!r}, "w").write("started")
open(wt + "/add.py", "w").write("def add(a, b):\\n    return a + b\\n")
print(json.dumps({{"type": "thread.started", "thread_id": "fake-thread"}}))
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5}}}}))
open(out, "w").write({report_text!r})
""")


class UrlCredentials(unittest.TestCase):
    """gitleaks does not look at scheme://user:password@host. The rule never keeps or prints the password."""

    def test_a_real_looking_password_blocks_and_is_never_kept(self):
        hits = cw.url_credentials(f"a\nDATABASE_URL=postgres://app:{SECRET}@db.internal:5432/x\n")  # gitleaks:allow
        self.assertEqual([(h.line, h.scheme, h.user, h.host, h.kind) for h in hits],
                         [(2, "postgres", "app", "db.internal", "block")])
        self.assertNotIn(SECRET, repr(hits))

    def test_loopback_hosts_are_only_noted(self):
        for url in ("postgres://postgres:postgres@127.0.0.1:5432/db", f"mysql://root:{SECRET}@localhost/db",  # gitleaks:allow
                    f"redis://app:{SECRET}@[::1]:6379"):  # gitleaks:allow
            with self.subTest(url=url):
                self.assertEqual([h.kind for h in cw.url_credentials(url)], ["note"])

    def test_placeholders_and_defaults_are_only_noted(self):
        for url in ("postgres://user:pass@host/db", "postgres://app:${DB_PASSWORD}@db.internal/x",
                    "redis://:<password>@redis:6379", "amqp://guest:password@rabbit/",
                    "postgres://postgres:postgres@db:5432/app"):  # gitleaks:allow
            with self.subTest(url=url):
                self.assertEqual([h.kind for h in cw.url_credentials(url)], ["note"])

    def test_an_empty_user_still_counts(self):
        self.assertEqual([h.kind for h in cw.url_credentials(f"redis://:{SECRET}@cache.internal:6379/0")], ["block"])

    def test_urls_without_a_password_are_not_hits(self):
        self.assertEqual(cw.url_credentials("https://example.com/a?b=1 git@github.com:x/y.git ssh://git@host/repo"), [])

    def test_a_lookalike_of_localhost_is_not_loopback(self):
        self.assertEqual([h.kind for h in cw.url_credentials(f"postgres://app:{SECRET}@localhost.example.com/db")],  # gitleaks:allow
                         ["block"])


class Gitleaks(unittest.TestCase):
    def test_exit_0_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            gl, _ = fake_gitleaks(d, 0)
            r = cw.run_gitleaks(Path(d), str(gl))
            self.assertEqual((r.status, r.findings), ("clean", []))

    def test_exit_1_lists_findings_without_values(self):
        with tempfile.TemporaryDirectory() as d:
            gl, _ = fake_gitleaks(d, 1, [{"RuleID": "github-pat", "File": "a.txt", "StartLine": 3,
                                          "Secret": GH_TOKEN, "Match": "token=" + GH_TOKEN}])
            r = cw.run_gitleaks(Path(d), str(gl))
            self.assertEqual(r.status, "leaks")
            self.assertEqual(r.findings, [{"rule": "github-pat", "file": "a.txt", "line": 3}])
            self.assertNotIn(GH_TOKEN, repr(r))

    def test_any_other_exit_is_an_error_never_clean(self):
        """zsh word-splitting once made gitleaks exit 126; a broken scanner must never read as a clean one."""
        for code in (2, 126):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as d:
                gl, _ = fake_gitleaks(d, code)
                self.assertEqual(cw.run_gitleaks(Path(d), str(gl)).status, "error")

    def test_a_missing_binary_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cw.run_gitleaks(Path(d), str(Path(d, "no-such-gitleaks"))).status, "missing")
            self.assertEqual(cw.run_gitleaks(Path(d), None).status, "missing")

    def test_a_corrupt_report_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            gl, _ = fake_gitleaks(d, 1, raw="{not json")
            self.assertEqual(cw.run_gitleaks(Path(d), str(gl)).status, "error")

    def test_a_scan_that_runs_too_long_is_a_timeout_never_clean(self):
        """0.1.6: a timeout is its own status, so the lead is told to raise --scan-timeout, not to fix the scanner."""
        with tempfile.TemporaryDirectory() as d:
            gl, _ = fake_gitleaks(d, 0, sleep=5)
            r = cw.run_gitleaks(Path(d), str(gl), timeout=1)
            self.assertEqual(r.status, "timeout")
            self.assertIn("did not finish within 1s", r.detail)

    def test_it_scans_dot_from_the_target_so_gitleaksignore_matches(self):
        """pops-pet, 2026-11-19: .gitleaksignore fingerprints only match when gitleaks scans `.` from the repo root."""
        with tempfile.TemporaryDirectory() as d:
            gl, log = fake_gitleaks(d, 0)
            cw.run_gitleaks(Path(d), str(gl))
            call = json.loads(log.read_text().splitlines()[0])
            self.assertEqual(Path(call["cwd"]).resolve(), Path(d).resolve())
            self.assertEqual(call["argv"][:2], ["dir", "."])
            self.assertIn("--redact", call["argv"])

    @unittest.skipUnless(shutil.which("gitleaks"), "gitleaks is not installed")
    def test_positive_control_with_the_real_gitleaks(self):
        """The fakes prove the plumbing. Only the real binary proves the flags still work."""
        with tempfile.TemporaryDirectory() as d:
            Path(d, "notes.md").write_text(f"token: {GH_TOKEN}\n")
            r = cw.run_gitleaks(Path(d), shutil.which("gitleaks"))
            self.assertEqual(r.status, "leaks")
            self.assertEqual([f["rule"] for f in r.findings], ["github-pat"])
        with tempfile.TemporaryDirectory() as d:
            Path(d, "notes.md").write_text("nothing to see here\n")
            self.assertEqual(cw.run_gitleaks(Path(d), shutil.which("gitleaks")).status, "clean")


class ReportHead(unittest.TestCase):
    def test_first_line_of_prose_without_the_heading_marks(self):
        self.assertEqual(cw.report_head("\n\n# Implemented X\nmore\n"), "Implemented X")

    def test_fenced_blocks_are_skipped(self):
        self.assertEqual(cw.report_head("```text\nRUN v4\n```\nThe real summary\n"), "The real summary")

    def test_long_lines_are_clipped_with_three_plain_dots(self):
        head = cw.report_head("a" * 300)
        self.assertEqual(len(head), 160)
        self.assertTrue(head.endswith("..."))

    def test_an_empty_report_gives_an_empty_head(self):
        self.assertEqual(cw.report_head(""), "")
        self.assertEqual(cw.report_head("\n  \n"), "")

    def test_the_run_that_started_this(self):
        text = ("Implemented the specified one-item housing behavior, but verification is blocked by one stale test "
                "expectation that still requires two housing items.\n\nFiles changed:\n")
        self.assertIn("verification is blocked by one stale test", cw.report_head(text))

    def test_terminal_control_characters_are_removed(self):
        """The head is the worker's text, printed to the lead's terminal: no escape sequences get through."""
        self.assertEqual(cw.report_head("\x1b[31mRED\x1b[0m tests\x07 here\n"), "RED tests here")


class ResultLine(unittest.TestCase):
    def test_pass_without_tests_says_the_tool_did_not_run_them(self):
        line = cw.result_line("PASS", [], tests_run=False)
        self.assertTrue(line.startswith("RESULT  PASS"))
        self.assertIn("verify not run by the tool", line)

    def test_pass_after_green_tests_is_plain(self):
        self.assertEqual(cw.result_line("PASS", [], tests_run=True), "RESULT  PASS")

    def test_other_statuses_keep_their_reasons(self):
        self.assertEqual(cw.result_line("REVISE", ["a", "b"], tests_run=False), "RESULT  REVISE  (a; b)")
        self.assertEqual(cw.result_line("FAIL", [], tests_run=False), "RESULT  FAIL")


class SlotWait(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.held = [cw.acquire_slot(self.d, 2) for _ in range(2)]

    def tearDown(self):
        for fd, _ in self.held:
            os.close(fd)
        self.tmp.cleanup()

    def test_wait_0_is_todays_behaviour(self):
        sleeps = []
        with self.assertRaises(cw.SlotBusy):
            cw.acquire_slot_waiting(self.d, 2, 0, sleep=sleeps.append, say=lambda m: None)
        self.assertEqual(sleeps, [])

    def test_it_waits_until_a_slot_frees(self):
        said = []

        def sleep(_seconds):  # a run finishes while we wait
            fd, _ = self.held.pop(0)
            os.close(fd)

        fd, slot = cw.acquire_slot_waiting(self.d, 2, 600, interval=15, sleep=sleep, say=said.append)
        os.close(fd)
        self.assertEqual(slot, 1)
        self.assertEqual(len(said), 1)

    def test_it_gives_up_at_the_deadline(self):
        now, sleeps = [1000.0], []

        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds

        with self.assertRaises(cw.SlotBusy):
            cw.acquire_slot_waiting(self.d, 2, 40, interval=15, sleep=sleep, clock=lambda: now[0], say=lambda m: None)
        self.assertEqual(sleeps, [15, 15, 10])


class NeverTheRealCodex(unittest.TestCase):
    def test_the_worker_binary_is_a_dead_end_unless_a_test_sets_a_fake(self):
        self.assertEqual(cw.codex_bin(), os.environ["CODEX_WP_BIN"])
        self.assertFalse(Path(cw.codex_bin()).exists())


class Cli014(unittest.TestCase):
    def test_version(self):
        self.assertEqual(cw.VERSION, "0.1.7")

    def test_wait_flag(self):
        self.assertEqual(cw.build_parser().parse_args(["run", "wp.md", "--wait", "600"]).wait, 600)
        self.assertEqual(cw.build_parser().parse_args(["run", "wp.md"]).wait, 0)

    def test_no_secret_scan_needs_a_reason(self):
        a = cw.build_parser().parse_args(["run", "wp.md", "--no-secret-scan", "scratch repo, no secrets"])
        self.assertEqual(a.no_secret_scan, "scratch repo, no secrets")
        self.assertIsNone(cw.build_parser().parse_args(["run", "wp.md"]).no_secret_scan)

    def test_run_waits_then_reports_busy(self):
        with tempfile.TemporaryDirectory() as d:
            old_state, old_check = cw.STATE_DIR, cw.seat_check
            cw.STATE_DIR = Path(d, "state")
            cw.seat_check = lambda **kw: (cw.EXIT_PASS, [])
            held = [cw.acquire_slot(cw.STATE_DIR / "slots", cw.MAX_SLOTS) for _ in range(cw.MAX_SLOTS)]
            try:
                repo = make_repo(d)
                wp = Path(d, "wp.md")
                wp.write_text(WP_TEXT)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cw.main(["run", str(wp), "--repo", str(repo), "--wait", "1"])
                self.assertEqual(rc, cw.EXIT_BUSY)
                self.assertIn("WAIT", buf.getvalue())
            finally:
                for fd, _ in held:
                    os.close(fd)
                cw.STATE_DIR, cw.seat_check = old_state, old_check

    def test_a_negative_wait_is_a_usage_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            cw.build_parser().parse_args(["run", "wp.md", "--wait", "-5"])
        self.assertIn("argument --wait", err.getvalue())  # rejected as a bad value, not as an unknown flag

    def test_after_a_wait_the_seat_is_checked_again_and_the_slot_released_on_hold(self):
        """A GO from before a long wait may be stale. Re-check; if no longer GO, give the slot back."""
        with tempfile.TemporaryDirectory() as d:
            old_state, old_check, old_waiting = cw.STATE_DIR, cw.seat_check, cw.acquire_slot_waiting
            cw.STATE_DIR = Path(d, "state")
            calls = []

            def seat(**kw):
                calls.append(kw)
                return (cw.EXIT_PASS, []) if len(calls) == 1 else (cw.EXIT_HOLD, ["quota HOLD"])

            held = [cw.acquire_slot(cw.STATE_DIR / "slots", cw.MAX_SLOTS) for _ in range(cw.MAX_SLOTS)]

            def waiting(directory, n, wait_s, **kw):
                """A run finishes during the wait. It used to be a 0.3 s timer, which under load fired before the
                first try, so the run never waited, skipped the re-check and dispatched a real worker."""
                os.close(held.pop(0)[0])
                return cw.acquire_slot(directory, n)

            cw.seat_check, cw.acquire_slot_waiting = seat, waiting
            try:
                repo = make_repo(d)
                wp = Path(d, "wp.md")
                wp.write_text(WP_TEXT)
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = cw.main(["run", str(wp), "--repo", str(repo), "--wait", "1"])
                self.assertEqual(rc, cw.EXIT_HOLD)
                self.assertEqual(len(calls), 2)
                fd, _ = cw.acquire_slot(cw.STATE_DIR / "slots", cw.MAX_SLOTS)  # the slot was given back
                os.close(fd)
            finally:
                for fd, _ in held:
                    os.close(fd)
                cw.STATE_DIR, cw.seat_check, cw.acquire_slot_waiting = old_state, old_check, old_waiting

    def test_readme_documents_0_1_4(self):
        text = Path(__file__).with_name("README.md").read_text()
        for needle in ("--wait", "--no-secret-scan", "not run by the tool", "outside the worktree"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class UrlRuleSuppression(unittest.TestCase):
    """pops-pet, 2026-11-20: a README placeholder blocked a dispatch, and neither gitleaks:allow nor .gitleaksignore
    could clear it because the URL rule ignored both, while auto mode refuses an AI's --no-secret-scan. A reviewed,
    committed exception must clear a URL hit exactly as it clears a gitleaks hit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.gl, _ = fake_gitleaks(self.d, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, name, text):
        (self.repo / name).write_text(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", f"add {name}")

    def test_a_gitleaks_allow_marker_turns_the_hit_into_a_note(self):
        self.commit("README.md", f"DB=postgres://app:{SECRET}@db.internal/x  # gitleaks:allow\n")
        r = cw.secret_preflight(self.repo, "", str(self.gl))
        self.assertEqual(r["blocking"], [])
        self.assertEqual([(n["file"], n["line"]) for n in r["noted"]], [("README.md", 1)])
        self.assertIn("gitleaks:allow", r["noted"][0]["why"])

    def test_a_gitleaksignore_fingerprint_turns_the_hit_into_a_note(self):
        self.commit("config.txt", f"x\nDB=postgres://app:{SECRET}@db.internal/x\n")  # gitleaks:allow
        self.commit(".gitleaksignore", "# reviewed: a placeholder\nconfig.txt:url-credential:2\n")
        r = cw.secret_preflight(self.repo, "", str(self.gl))
        self.assertEqual(r["blocking"], [])
        self.assertIn(".gitleaksignore", r["noted"][0]["why"])

    def test_an_unmarked_line_still_blocks(self):
        self.commit("config.txt", f"A=postgres://app:{SECRET}@db.internal/x  # gitleaks:allow\n"
                                  f"B=postgres://app:{SECRET}@db.internal/y\n")  # gitleaks:allow
        r = cw.secret_preflight(self.repo, "", str(self.gl))
        self.assertEqual([(b["file"], b["line"]) for b in r["blocking"]], [("config.txt", 2)])

    def test_readme_documents_0_1_5(self):
        text = Path(__file__).with_name("README.md").read_text()
        for needle in ("url-credential", "gitleaks:allow", "for a human"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class VerifyState(unittest.TestCase):
    """`codex-wp verify` wrote its results but left status PASS on a red verify, so every reader had to dig into
    verify_results. The record now says what the lead's verify found."""

    def test_cmd_verify_records_green_and_red(self):
        with tempfile.TemporaryDirectory() as d:
            old = cw.STATE_DIR
            cw.STATE_DIR = Path(d, "state")
            try:
                wt = Path(d, "wt")
                wt.mkdir()
                run = cw.STATE_DIR / "runs" / "r1"
                run.mkdir(parents=True)
                for cmds, state in ((["true"], "green"), (["true", "false"], "red")):
                    with self.subTest(state=state):
                        (run / "meta.json").write_text(json.dumps(
                            {"run_id": "r1", "worktree": str(wt), "verify_cmds": cmds, "status": "PASS"}))
                        with contextlib.redirect_stdout(io.StringIO()):
                            cw.cmd_verify(argparse.Namespace(run="r1", verbose=False))
                        self.assertEqual(json.loads((run / "meta.json").read_text())["verify_state"], state)
            finally:
                cw.STATE_DIR = old


def gitleaks_calls(log, cwd):
    """The fake gitleaks calls made from `cwd`: the scans of that tree."""
    if not Path(log).exists():
        return []
    calls = [json.loads(ln) for ln in Path(log).read_text().splitlines()]
    return [c for c in calls if Path(c["cwd"]).resolve() == Path(cwd).resolve()]


def canonical(entries):
    return sorted(json.dumps(e, sort_keys=True) for e in entries)


class PreflightCache(unittest.TestCase):
    """2026-11-19: the preflight rescanned the whole base tree on every dispatch: 76 s on the clinic app, and past
    the 300 s cap on pops-vet-oracle (24,747 files, 778 MB), which then could not dispatch at all. A finished scan is
    now cached per base TREE, keyed with the scanner's identity and codex-wp's version. The WP text is always
    scanned fresh."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.cache = self.d / "cache"
        self.gl, self.log = fake_gitleaks(self.d, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, name, text):
        (self.repo / name).write_text(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", f"add {name}")

    def scan(self, wp_text="", gl=None, **kw):
        return cw.secret_preflight(self.repo, wp_text, str(gl or self.gl), cache_dir=self.cache, **kw)

    def other_gitleaks(self, name, *args, **kw):
        d = self.d / name
        d.mkdir()
        return fake_gitleaks(d, *args, **kw)

    def entries(self):
        return sorted(self.cache.glob("*.json"))

    def test_the_result_says_what_happened(self):
        r = self.scan()
        for key in ("blocking", "noted", "error", "cached", "tree", "timed_out", "scan_s"):
            with self.subTest(key=key):
                self.assertIn(key, r)
        self.assertEqual(r["tree"], sh(self.repo, "git", "rev-parse", "HEAD^{tree}"))
        self.assertEqual((r["cached"], r["timed_out"], r["error"]), (False, False, None))

    def test_a_second_scan_of_the_same_tree_is_a_cache_hit(self):
        self.assertFalse(self.scan()["cached"])
        self.assertTrue(self.scan()["cached"])
        self.assertEqual(len(gitleaks_calls(self.log, self.repo)), 1)

    def test_the_key_is_the_tree_not_the_commit(self):
        self.scan()
        sh(self.repo, "git", "commit", "-q", "--allow-empty", "-m", "same tree, new commit")
        self.assertTrue(self.scan()["cached"])

    def test_a_new_tree_is_scanned(self):
        self.scan()
        self.commit("notes.md", "more\n")
        self.assertFalse(self.scan()["cached"])
        self.assertEqual(len(gitleaks_calls(self.log, self.repo)), 2)

    def test_findings_come_back_from_the_cache_unchanged(self):
        self.commit("test.env", "DB=postgres://postgres:postgres@127.0.0.1:5432/test\n")  # gitleaks:allow
        self.commit("config.txt", f"DB=postgres://app:{SECRET}@db.internal/x\n")  # gitleaks:allow
        fresh, cached = self.scan(), self.scan()
        self.assertTrue(cached["cached"])
        for key in ("blocking", "noted"):
            with self.subTest(key=key):
                self.assertEqual(canonical(fresh[key]), canonical(cached[key]))
        self.assertEqual([(b["file"], b["line"]) for b in cached["blocking"]], [("config.txt", 1)])
        self.assertEqual([n["file"] for n in cached["noted"]], ["test.env"])

    def test_a_gitleaks_finding_is_cached_too(self):
        gl, log = self.other_gitleaks("leaky", 1, [{"RuleID": "github-pat", "File": "notes.md", "StartLine": 4,
                                                     "Secret": "REDACTED", "Match": "REDACTED"}])
        want = {"source": "worktree", "rule": "github-pat", "file": "notes.md", "line": 4}
        self.assertIn(want, self.scan(gl=gl)["blocking"])
        second = self.scan(gl=gl)
        self.assertTrue(second["cached"])
        self.assertIn(want, second["blocking"])
        self.assertEqual(len(gitleaks_calls(log, self.repo)), 1)

    def test_the_wp_text_is_always_scanned_fresh(self):
        self.scan()
        r = self.scan(wp_text=f"connect with postgres://app:{SECRET}@db.internal/x\n")  # gitleaks:allow
        self.assertTrue(r["cached"])
        self.assertEqual([b["source"] for b in r["blocking"]], ["wp"])

    def test_another_scanner_or_another_codex_wp_version_misses(self):
        self.scan()
        other, _ = self.other_gitleaks("other", 0)
        self.assertFalse(self.scan(gl=other)["cached"])
        with mock.patch.object(cw, "VERSION", cw.VERSION + "-next"):
            self.assertFalse(self.scan()["cached"])

    def test_a_gitleaks_config_from_the_environment_is_part_of_the_key(self):
        """GITLEAKS_CONFIG and GITLEAKS_CONFIG_TOML replace the repo's rules: a result made under other rules must
        not answer."""
        self.scan()
        rules = self.d / "rules.toml"
        rules.write_text("# rules one\n")
        with mock.patch.dict(os.environ, {"GITLEAKS_CONFIG": str(rules)}):
            self.assertFalse(self.scan()["cached"])
            self.assertTrue(self.scan()["cached"])
            rules.write_text("# rules two\n")
            self.assertFalse(self.scan()["cached"])
        with mock.patch.dict(os.environ, {"GITLEAKS_CONFIG_TOML": "# inline rules\n"}):
            self.assertFalse(self.scan()["cached"])

    def test_rescan_ignores_the_cache_and_refreshes_it(self):
        self.scan()
        self.assertFalse(self.scan(rescan=True)["cached"])
        self.assertEqual(len(gitleaks_calls(self.log, self.repo)), 2)
        self.assertTrue(self.scan()["cached"])

    def test_a_failed_scan_is_not_cached(self):
        broken, _ = self.other_gitleaks("broken", 126)
        self.assertTrue(self.scan(gl=broken)["error"])
        again = self.scan(gl=broken)
        self.assertFalse(again["cached"])
        self.assertTrue(again["error"])
        self.assertEqual(self.entries(), [])

    def test_a_timed_out_scan_is_not_cached_and_says_so(self):
        slow, _ = self.other_gitleaks("slow", 0, sleep=2)
        r = self.scan(gl=slow, timeout=1)
        self.assertTrue(r["timed_out"])
        self.assertIn("did not finish within 1s", r["error"])
        self.assertFalse(r["cached"])
        self.assertEqual(self.entries(), [])

    def test_the_cache_holds_findings_from_the_tree_only_and_no_secret_value(self):
        self.commit("config.txt", f"DB=postgres://app:{SECRET}@db.internal/x\n")  # gitleaks:allow
        self.scan(wp_text=f"also postgres://app:{SECRET}@db.internal/y\n")  # gitleaks:allow
        (entry,) = self.entries()
        self.assertRegex(entry.name, r"^[0-9a-f]{64}\.json$")
        text = entry.read_text()
        self.assertNotIn(SECRET, text)
        data = json.loads(text)
        self.assertEqual({e["source"] for e in data["blocking"] + data["noted"]}, {"worktree"})
        self.assertEqual(data["tree"], sh(self.repo, "git", "rev-parse", "HEAD^{tree}"))

    def test_a_hit_returns_the_stored_entry_without_reading_the_tree(self):
        """An entry edited by hand comes back as stored: the hit skipped the URL scan as well as gitleaks."""
        self.scan()
        (entry,) = self.entries()
        data = json.loads(entry.read_text())
        data["noted"].append({"source": "worktree", "rule": "url-credential", "file": "sentinel.txt", "line": 7,
                              "why": "loopback host"})
        entry.write_text(json.dumps(data))
        r = self.scan()
        self.assertTrue(r["cached"])
        self.assertIn("sentinel.txt", [n["file"] for n in r["noted"]])

    def test_a_corrupt_entry_is_a_miss_and_is_replaced(self):
        self.scan()
        (entry,) = self.entries()
        for bad in ("{not json", '{"blocking": "x", "noted": []}', "[]"):
            with self.subTest(bad=bad):
                entry.write_text(bad)
                self.assertFalse(self.scan()["cached"])
                self.assertTrue(self.scan()["cached"])

    def test_entries_older_than_14_days_go_when_a_new_one_is_written(self):
        self.cache.mkdir(parents=True)
        old, recent = self.cache / ("0" * 64 + ".json"), self.cache / ("1" * 64 + ".json")
        now = time.time()
        for path, age_days in ((old, 15), (recent, 1)):
            path.write_text("{}")
            os.utime(path, (now - age_days * 86400, now - age_days * 86400))
        self.scan()
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())
        self.assertEqual(len(self.entries()), 2)

    def test_without_a_cache_dir_nothing_is_cached(self):
        cw.secret_preflight(self.repo, "", str(self.gl))
        r = cw.secret_preflight(self.repo, "", str(self.gl))
        self.assertFalse(r["cached"])
        self.assertEqual(len(gitleaks_calls(self.log, self.repo)), 2)


class Cli016(unittest.TestCase):
    def test_scan_timeout_flag_and_its_default(self):
        p = cw.build_parser()
        self.assertEqual(p.parse_args(["run", "wp.md", "--scan-timeout", "1800"]).scan_timeout, 1800)
        self.assertEqual(p.parse_args(["run", "wp.md"]).scan_timeout, cw.DEFAULT_SCAN_TIMEOUT_S)
        self.assertEqual(cw.DEFAULT_SCAN_TIMEOUT_S, 900)

    def test_scan_timeout_must_be_a_positive_integer(self):
        for bad in ("0", "-5", "ten"):
            with self.subTest(bad=bad):
                err = io.StringIO()
                with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
                    cw.build_parser().parse_args(["run", "wp.md", "--scan-timeout", bad])
                self.assertIn("argument --scan-timeout", err.getvalue())

    def test_rescan_flag(self):
        self.assertTrue(cw.build_parser().parse_args(["run", "wp.md", "--rescan"]).rescan)
        self.assertFalse(cw.build_parser().parse_args(["run", "wp.md"]).rescan)

    def test_readme_documents_0_1_6(self):
        text = Path(__file__).with_name("README.md").read_text()
        for needle in ("--scan-timeout", "--rescan", "base tree", "cached"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


LEAKED = "Lk7" + "pQ2wZx9Rt4"  # made up, never a real credential; split so no scanner sees it whole


def h12(value):
    return hashlib.sha256(value.encode()).hexdigest()[:12]


class LeakedList(unittest.TestCase):
    """The known-leaked list is machine-local: ~/.codex-wp/leaked-sha12.txt, or $CODEX_WP_LEAKED. One sha256[:12]
    prefix per line, an optional label after it, # comments. A list that cannot be read must stop dispatch, never
    weaken the check in silence."""

    def test_prefixes_labels_and_comments(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "leaked.txt")
            p.write_text(f"# RPRO-16612, values never printed\n\n{h12(LEAKED)}  influx/pg-super/redis\n"
                         f"{h12('other-value').upper()}\n")
            self.assertEqual(cw.load_leaked_list(p), {h12(LEAKED): "influx/pg-super/redis", h12("other-value"): ""})

    def test_a_missing_list_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cw.load_leaked_list(Path(d, "none.txt")), {})

    def test_a_malformed_line_fails_loudly(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "leaked.txt")
            p.write_text(f"{h12(LEAKED)}\nnot-a-hash\n")
            with self.assertRaises(ValueError) as ctx:
                cw.load_leaked_list(p)
            self.assertIn("line 2", str(ctx.exception))

    def test_the_path_follows_state_dir_or_the_environment(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cw, "STATE_DIR", Path(d)):
            with mock.patch.dict(os.environ, {"CODEX_WP_LEAKED": ""}):
                self.assertEqual(cw.leaked_list_path(), Path(d, "leaked-sha12.txt"))
            with mock.patch.dict(os.environ, {"CODEX_WP_LEAKED": str(Path(d, "x.txt"))}):
                self.assertEqual(cw.leaked_list_path(), Path(d, "x.txt"))


class KnownLeaked(unittest.TestCase):
    """rpro-ent, 2026-11-20 (RPRO-16612): live cluster passwords sat in 35 RPRO service repos disguised as
    <32hex>_mockup and mock_<value>. Stock gitleaks misses both shapes, so the preflight let them through to workers.
    Every token is now hashed in memory and compared with the known-leaked list; a hit always blocks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.gl, _ = fake_gitleaks(self.d, 0)
        self.leaked = {h12(LEAKED): "influx"}

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, name, text):
        (self.repo / name).write_text(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", f"add {name}")

    def scan(self, wp_text="", **kw):
        return cw.secret_preflight(self.repo, wp_text, str(self.gl), **kw)

    @staticmethod
    def known(r, source="worktree"):
        return [b for b in r["blocking"] if b["rule"] == "known-leaked" and b["source"] == source]

    def test_every_disguise_is_found_by_hash_and_no_value_is_kept(self):
        self.commit("settings.js", "\n".join([
            f"password: '{LEAKED}',",
            f"INFLUX_PASSWORD={LEAKED}_mockup",
            f"REDIS_PASSWORD=mock_{LEAKED}",
            f"url=redis://u:{LEAKED}@cache.internal:6379",  # gitleaks:allow
            '{"output":"A=' + LEAKED + '\\nB=x"}',  # a JSON-escaped newline glues the value to the next token
            "nothing to see here",
        ]) + "\n")
        r = self.scan(leaked=self.leaked)
        self.assertEqual([(b["line"], b["label"]) for b in self.known(r)],
                         [(1, "influx"), (2, "influx"), (3, "influx"), (4, "influx"), (5, "influx")])
        self.assertNotIn(LEAKED, json.dumps(r))

    def test_a_marker_cannot_allow_a_known_leaked_value(self):
        self.commit("config.txt", f"X={LEAKED}  # gitleaks:allow\n")
        self.commit(".gitleaksignore", "config.txt:known-leaked:1\n")
        self.assertEqual([b["line"] for b in self.known(self.scan(leaked=self.leaked))], [1])

    def test_the_wp_text_is_checked_too(self):
        r = self.scan(wp_text=f"- Context: the cluster password is mock_{LEAKED}\n", leaked=self.leaked)
        self.assertEqual([(b["file"], b["line"]) for b in self.known(r, "wp")], [("wp.md", 1)])
        self.assertNotIn(LEAKED, json.dumps(r))

    def test_an_empty_or_absent_list_checks_nothing(self):
        self.commit("config.txt", f"X={LEAKED}\n")
        self.assertEqual(self.known(self.scan(leaked={})), [])
        self.assertEqual(self.known(self.scan()), [])

    def test_a_longer_token_is_not_a_hit(self):
        self.commit("config.txt", f"Y={LEAKED}ff\nsha={'a' * 40}\n")
        self.assertEqual(self.known(self.scan(leaked=self.leaked)), [])

    def test_the_list_is_part_of_the_cache_key(self):
        self.commit("config.txt", f"X=mock_{LEAKED}\n")
        cache = self.d / "cache"
        self.assertFalse(self.scan(leaked={}, cache_dir=cache)["cached"])
        self.assertTrue(self.scan(leaked={}, cache_dir=cache)["cached"])
        r = self.scan(leaked=self.leaked, cache_dir=cache)
        self.assertFalse(r["cached"])  # a new list must rescan, or a cached "clean" would hide the leak
        self.assertEqual([b["line"] for b in self.known(r)], [1])
        self.assertTrue(self.scan(leaked=self.leaked, cache_dir=cache)["cached"])


class MockupShape(unittest.TestCase):
    """A disguised value that is not on the list yet: 32 hex characters with a _mockup suffix is the shape the RPRO
    repos used. Unlike a known-leaked hit, a shape can be wrong, so it honours gitleaks:allow and .gitleaksignore."""

    HEX = "0123456789abcdef" * 2

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.gl, _ = fake_gitleaks(self.d, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, name, text):
        (self.repo / name).write_text(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", f"add {name}")

    def scan(self, wp_text=""):
        return cw.secret_preflight(self.repo, wp_text, str(self.gl))

    def test_the_shape_blocks_without_keeping_the_value(self):
        self.commit("settings.js", f"x\nINFLUX_PASSWORD={self.HEX}_mockup\n")
        r = self.scan()
        self.assertEqual([(b["rule"], b["file"], b["line"]) for b in r["blocking"]], [("mockup-hex", "settings.js", 2)])
        self.assertNotIn(self.HEX, json.dumps(r))

    def test_longer_hex_or_a_longer_suffix_is_not_the_shape(self):
        self.commit("settings.js", f"SHA={'a' * 40}_mockup\nnope={self.HEX}_mockups\n")
        self.assertEqual(self.scan()["blocking"], [])

    def test_the_shape_honours_markers(self):
        self.commit("a.js", f"P={self.HEX}_mockup  # gitleaks:allow\n")
        self.commit("b.js", f"P={self.HEX}_mockup\n")
        self.commit(".gitleaksignore", "b.js:mockup-hex:1\n")
        r = self.scan()
        self.assertEqual(r["blocking"], [])
        self.assertEqual(sorted(n["file"] for n in r["noted"] if n["rule"] == "mockup-hex"), ["a.js", "b.js"])

    def test_the_wp_text_is_checked(self):
        r = self.scan(wp_text=f"use {self.HEX}_mockup\n")
        self.assertEqual([(b["source"], b["rule"]) for b in r["blocking"]], [("wp", "mockup-hex")])


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ProcessGroups(unittest.TestCase):
    """pops-vet 1165, 2026-11-20: a DB verify command ran past its 900 s timeout under load. subprocess.run killed only
    the shell, so the script's EXIT trap never ran and its postgres container stayed up; its children also held the
    output pipe open. A timed-out command now gets SIGTERM on its whole process group, a grace period, then SIGKILL,
    and a timeout is reported as None, never as an exit code."""

    def test_constants(self):
        self.assertEqual((cw.KILL_GRACE_S, cw.VERIFY_TIMEOUT_S, cw.SETUP_TIMEOUT_S), (10, 900, 1800))

    def test_sigterm_reaches_the_group_so_an_exit_trap_runs(self):
        with tempfile.TemporaryDirectory() as d:
            t0 = time.monotonic()
            res = cw.run_commands([f"bash -c 'trap \"touch {d}/cleaned\" EXIT; sleep 20'"], Path(d), timeout=1)
            self.assertLess(time.monotonic() - t0, 12)
            self.assertIsNone(res[0][1])
            self.assertIn("timeout after 1s", res[0][2])
            self.assertTrue(Path(d, "cleaned").exists(), "SIGTERM first, so the EXIT trap ran")

    def test_a_background_child_does_not_outlive_the_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            t0 = time.monotonic()
            cw.run_commands([f"sleep 20 & echo $! > {d}/child.pid; wait"], Path(d), timeout=1)
            self.assertLess(time.monotonic() - t0, 12)
            pid = int(Path(d, "child.pid").read_text())
            deadline = time.monotonic() + 3
            while alive(pid) and time.monotonic() < deadline:
                time.sleep(0.1)
            self.assertFalse(alive(pid))

    def test_a_command_that_ignores_sigterm_is_killed_after_the_grace(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cw, "KILL_GRACE_S", 1):
            t0 = time.monotonic()
            res = cw.run_commands(["trap '' TERM; sleep 20"], Path(d), timeout=1)
            self.assertLess(time.monotonic() - t0, 12)
            self.assertIsNone(res[0][1])

    def test_a_setup_timeout_stops_the_group_too(self):
        with tempfile.TemporaryDirectory() as d:
            ok, detail = cw.run_setup(f"bash -c 'trap \"touch {d}/cleaned\" EXIT; sleep 20'", Path(d), timeout=1)
            self.assertFalse(ok)
            self.assertIn("timed out after 1s", detail)
            self.assertTrue(Path(d, "cleaned").exists())

    def test_a_timeout_on_base_is_not_a_red_test(self):
        """A test that hangs used to pass the --tdd gate: the timeout counted as 'fails on base'."""
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cw, "STATE_DIR", Path(d, "state")), \
                mock.patch.object(cw, "VERIFY_TIMEOUT_S", 1):
            repo = make_repo(d)
            ok, detail = cw.base_check(repo, "HEAD", ["sleep 20"], "r1")
            self.assertFalse(ok)
            self.assertIn("timed out", detail)

    def test_verify_records_a_timeout_as_its_own_state(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cw, "STATE_DIR", Path(d, "state")), \
                mock.patch.object(cw, "VERIFY_TIMEOUT_S", 1):
            wt = Path(d, "wt")
            wt.mkdir()
            run = cw.STATE_DIR / "runs" / "r1"
            run.mkdir(parents=True)
            (run / "meta.json").write_text(json.dumps(
                {"run_id": "r1", "worktree": str(wt), "verify_cmds": ["sleep 20"], "status": "PASS"}))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = cw.cmd_verify(argparse.Namespace(run="r1", verbose=False))
            meta = json.loads((run / "meta.json").read_text())
            self.assertEqual(rc, cw.EXIT_REVISE)
            self.assertEqual(meta["verify_state"], "timeout")
            self.assertIsNone(meta["verify_results"][0][1])
            self.assertIn("TIME", out.getvalue())


FAKE_CODEX_SH = """#!/bin/sh
case "$1" in
  --version) echo "codex-cli {version}" ;;
  login) echo "Logged in using ChatGPT" ;;
  *) echo "fake codex: no real call in tests" >&2; exit 3 ;;
esac
"""


class CodexBinary(unittest.TestCase):
    """rpro-saas, 2026-11-20: this Mac has /opt/homebrew/bin/codex 0.144.1 and ~/.bun/bin/codex 0.166.0. A window whose
    PATH found Homebrew first ran 0.144.1, which gets an HTTP 400 on gpt-6.1-sol, while the selftest had passed on
    0.166.0. The binary that passed the selftest is now the one codex-wp runs, and check says when PATH differs."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.brew = self.fake("brew", "0.144.1")
        self.bun = self.fake("bun", "0.166.0")
        self.record = self.d / "selftest.json"
        env = {k: v for k, v in os.environ.items() if k != "CODEX_WP_BIN"}
        env["PATH"] = f"{self.d / 'brew'}:{self.d / 'bun'}:/usr/bin:/bin"
        self.patches = [mock.patch.dict(os.environ, env, clear=True),
                        mock.patch.object(cw, "SELFTEST_FILE", self.record)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def fake(self, name, version):
        (self.d / name).mkdir()
        return str(write_exec(self.d / name / "codex", FAKE_CODEX_SH.format(version=version)))

    def write_record(self, **kw):
        rec = {"codex_version": "codex-cli 0.166.0", "model": "gpt-6.1-sol", "ts": time.time(), "result": "PASS"}
        rec.update(kw)
        cw.write_selftest_record(self.record, rec)

    def test_without_a_record_the_first_codex_on_path_runs(self):
        self.assertEqual(cw.codex_bin(), self.brew)

    def test_a_passing_selftest_pins_the_binary_it_tested(self):
        self.write_record(codex_path=self.bun)
        self.assertEqual(cw.codex_bin(), self.bun)

    def test_a_failed_selftest_or_a_vanished_binary_does_not_pin(self):
        self.write_record(codex_path=self.bun, result="FAIL")
        self.assertEqual(cw.codex_bin(), self.brew)
        self.write_record(codex_path=str(self.d / "gone" / "codex"))
        self.assertEqual(cw.codex_bin(), self.brew)

    def test_the_environment_still_wins(self):
        self.write_record(codex_path=self.bun)
        with mock.patch.dict(os.environ, {"CODEX_WP_BIN": self.brew}):
            self.assertEqual(cw.codex_bin(), self.brew)

    def test_check_says_which_binary_runs_and_what_path_would_find(self):
        self.write_record(codex_path=self.bun)
        with mock.patch.object(cw, "STATE_DIR", self.d / "state"), \
                mock.patch.dict(os.environ, {"CODEX_HOME": str(self.d / "codex-home")}):
            _, lines = cw.seat_check(model="gpt-6.1-sol")
        text = "\n".join(lines)
        self.assertIn(f"codex   {self.bun} (codex-cli 0.166.0)", text)
        self.assertIn(f"PATH finds {self.brew}", text)
        self.assertIn("0.144.1", text)
        self.assertIn("selftest PASS", text)
        self.assertIn("leaked  ", text)  # the known-leaked list state is part of the seat check

    def test_selftest_records_the_binary_it_tested_and_hands_it_to_the_run(self):
        real_run, real_mkdtemp = subprocess.run, tempfile.mkdtemp
        handed = []

        def fake_run(argv, *args, **kw):
            if isinstance(argv, list) and len(argv) > 2 and argv[2] == "run":
                handed.append((kw.get("env") or {}).get("CODEX_WP_BIN"))
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")
            return real_run(argv, *args, **kw)

        with mock.patch.dict(os.environ, {"CODEX_WP_BIN": self.bun}), \
                mock.patch.object(cw.subprocess, "run", fake_run), \
                mock.patch.object(cw.tempfile, "mkdtemp", lambda prefix=None: real_mkdtemp(prefix=prefix, dir=self.d)), \
                contextlib.redirect_stdout(io.StringIO()):
            cw.cmd_selftest(argparse.Namespace(model="gpt-6.1-sol"))
        self.assertEqual(handed, [self.bun])
        record = cw.read_selftest_record(self.record)
        self.assertEqual(record["codex_path"], self.bun)
        self.assertEqual(record["result"], "FAIL")  # the fake run printed no RUN line, so nothing passed


class Cli017(unittest.TestCase):
    def test_readme_documents_0_1_7(self):
        text = Path(__file__).with_name("README.md").read_text()
        for needle in ("leaked-sha12.txt", "known-leaked", "mockup-hex", "process group", "passed the selftest"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


class RunFlow(unittest.TestCase):
    """_run_locked end to end with a fake Codex and a fake gitleaks: no network, no quota."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.mark = self.d / "worker-started"
        self.old_state = cw.STATE_DIR
        cw.STATE_DIR = self.d / "state"
        self.old_env = {k: os.environ.get(k) for k in ("CODEX_WP_BIN", "CODEX_WP_GITLEAKS", "CODEX_HOME",
                                                       "CODEX_WP_LEAKED")}
        os.environ["CODEX_HOME"] = str(self.d / "codex-home")
        os.environ.pop("CODEX_WP_LEAKED", None)  # the run must read only the test's own list, never the machine's
        self.gl, self.gl_log = fake_gitleaks(self.d, 0)
        os.environ["CODEX_WP_GITLEAKS"] = str(self.gl)

    def tearDown(self):
        cw.STATE_DIR = self.old_state
        for k, v in self.old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def commit_file(self, name, text):
        (self.repo / name).write_text(text)
        sh(self.repo, "git", "add", name)
        sh(self.repo, "git", "commit", "-q", "-m", f"add {name}")

    def run_locked(self, report_text="Implemented add().\n", wp_text=WP_TEXT, **kw):
        os.environ["CODEX_WP_BIN"] = str(fake_codex(self.d, report_text, self.mark))
        args = dict(wp="wp.md", repo=str(self.repo), base="HEAD", model="fake-model", effort=None, tdd=False,
                    setup=None, verify_now=False, timeout=60, force_pace=None, follow=False, wait=0,
                    no_secret_scan=None, scan_timeout=60, rescan=False)
        args.update(kw)
        runs = cw.STATE_DIR / "runs"
        before = set(runs.iterdir()) if runs.exists() else set()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cw._run_locked(argparse.Namespace(**args), cw.parse_wp(wp_text), self.repo, 1)
        (run_dir,) = set(runs.iterdir()) - before  # the run this call made, also when a test makes several
        return rc, buf.getvalue(), json.loads((run_dir / "meta.json").read_text())

    def test_pass_says_the_tool_did_not_run_the_tests_and_quotes_the_report(self):
        rc, out, meta = self.run_locked("Implemented add(), but verification is blocked by one stale test.\nMore.\n")
        self.assertEqual(rc, cw.EXIT_PASS)
        line = next(ln for ln in out.splitlines() if ln.startswith("RESULT"))
        self.assertTrue(line.startswith("RESULT  PASS"))
        self.assertIn("verify not run by the tool", line)
        self.assertIn("  report   Implemented add(), but verification is blocked by one stale test.", out)
        self.assertEqual(meta["report_head"], "Implemented add(), but verification is blocked by one stale test.")
        self.assertEqual(meta["verify_state"], "not run")
        self.assertEqual(meta["timeout_s"], 60)  # the six SIGTERM runs could not be diagnosed: nobody knew this value

    def test_verify_now_green_is_a_plain_pass(self):
        rc, out, meta = self.run_locked(verify_now=True)
        self.assertEqual(rc, cw.EXIT_PASS)
        self.assertEqual(next(ln for ln in out.splitlines() if ln.startswith("RESULT")).strip(), "RESULT  PASS")
        self.assertEqual(meta["verify_state"], "green")

    def test_a_url_credential_blocks_the_worker_before_setup_runs(self):
        self.commit_file("config.txt", f"DATABASE_URL=postgres://app:{SECRET}@db.internal:5432/x\n")  # gitleaks:allow
        rc, out, meta = self.run_locked(setup="touch SETUP_RAN")
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertEqual(meta["status"], "PRECONDITION")
        self.assertFalse(self.mark.exists(), "the worker must not start")
        self.assertFalse(Path(meta["worktree"], "SETUP_RAN").exists(), "the scan runs before --setup")
        self.assertEqual([(b["source"], b["file"], b["line"], b["rule"]) for b in meta["secret_scan"]["blocking"]],
                         [("worktree", "config.txt", 1, "url-credential")])
        self.assertNotIn(SECRET, out)
        self.assertNotIn(SECRET, json.dumps(meta))
        self.assertIn("codex-wp done", out)  # the blocked run says how to clean up its worktree
        self.assertIn("gitleaks:allow", out)  # the reviewed-exception path an AI lead CAN take
        self.assertIn("for a human", out)  # auto mode refuses an AI's --no-secret-scan: say so up front

    def test_a_credential_in_the_wp_text_blocks(self):
        wp_text = WP_TEXT + f"- Note: connect with postgres://app:{SECRET}@db.internal/x\n"  # gitleaks:allow
        rc, out, meta = self.run_locked(wp_text=wp_text)
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists())
        self.assertIn("wp", [b["source"] for b in meta["secret_scan"]["blocking"]])
        self.assertNotIn(SECRET, out)

    def test_loopback_defaults_are_noted_and_the_worker_runs(self):
        self.commit_file("test.env", "DB=postgres://postgres:postgres@127.0.0.1:5432/test\n")  # gitleaks:allow
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PASS)
        self.assertTrue(self.mark.exists())
        self.assertEqual(meta["secret_scan"]["blocking"], [])
        self.assertEqual([n["file"] for n in meta["secret_scan"]["noted"]], ["test.env"])
        self.assertIn("noted", out)  # an allowance is visible, never silent

    def test_a_gitleaks_finding_blocks(self):
        gl, _ = fake_gitleaks(self.d, 1, [{"RuleID": "github-pat", "File": "notes.md", "StartLine": 4,
                                           "Secret": "REDACTED", "Match": "REDACTED"}])
        os.environ["CODEX_WP_GITLEAKS"] = str(gl)
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists())
        self.assertIn({"source": "worktree", "rule": "github-pat", "file": "notes.md", "line": 4},
                      meta["secret_scan"]["blocking"])

    def test_a_gitleaks_error_fails_closed(self):
        gl, _ = fake_gitleaks(self.d, 126)
        os.environ["CODEX_WP_GITLEAKS"] = str(gl)
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists())
        self.assertTrue(meta["secret_scan"]["error"])

    def test_missing_gitleaks_fails_closed_with_a_hint(self):
        os.environ["CODEX_WP_GITLEAKS"] = str(self.d / "no-such-gitleaks")
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertIn("gitleaks", meta["secret_scan"]["error"])
        self.assertIn("--no-secret-scan", out)
        self.assertIn("for a human", meta["secret_scan"]["error"])  # 0.1.6: the last hint that still offered it to an AI

    def test_no_secret_scan_is_recorded_with_its_reason(self):
        os.environ["CODEX_WP_GITLEAKS"] = str(self.d / "no-such-gitleaks")
        rc, out, meta = self.run_locked(no_secret_scan="scratch repo, no secrets")
        self.assertEqual(rc, cw.EXIT_PASS)
        self.assertEqual(meta["secret_scan"], {"skipped": "scratch repo, no secrets"})

    def test_gitleaks_scans_dot_from_the_worktree_root(self):
        rc, out, meta = self.run_locked()
        calls = [json.loads(ln) for ln in self.gl_log.read_text().splitlines()]
        wt = Path(meta["worktree"]).resolve()
        self.assertEqual([c["argv"][:2] for c in calls if Path(c["cwd"]).resolve() == wt], [["dir", "."]])

    # 0.1.6: the preflight cache, --scan-timeout, quieter notes

    def test_a_second_run_on_the_same_base_uses_the_cache(self):
        rc1, out1, meta1 = self.run_locked()
        rc2, out2, meta2 = self.run_locked()
        self.assertEqual((rc1, rc2), (cw.EXIT_PASS, cw.EXIT_PASS))
        self.assertIn("SECRETS scanned base tree", out1)
        self.assertNotIn("cache hit", out1)
        self.assertIn("SECRETS cache hit: base tree", out2)
        self.assertEqual((meta1["secret_scan"]["cached"], meta2["secret_scan"]["cached"]), (False, True))
        self.assertEqual(gitleaks_calls(self.gl_log, meta2["worktree"]), [])  # the second worktree was never scanned
        self.assertTrue(list((cw.STATE_DIR / "cache" / "preflight").glob("*.json")))  # the cache lives in STATE_DIR

    def test_a_blocked_tree_is_blocked_again_from_the_cache(self):
        self.commit_file("config.txt", f"DATABASE_URL=postgres://app:{SECRET}@db.internal:5432/x\n")  # gitleaks:allow
        self.run_locked()
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertTrue(meta["secret_scan"]["cached"])
        self.assertEqual([(b["file"], b["line"]) for b in meta["secret_scan"]["blocking"]], [("config.txt", 1)])
        self.assertNotIn(SECRET, out)

    def test_rescan_scans_the_tree_again(self):
        self.run_locked()
        rc, out, meta = self.run_locked(rescan=True)
        self.assertFalse(meta["secret_scan"]["cached"])
        self.assertEqual(len(gitleaks_calls(self.gl_log, meta["worktree"])), 1)

    def test_a_scan_timeout_fails_closed_and_says_how_to_go_on(self):
        slow, _ = fake_gitleaks(self.d, 0, sleep=2)
        os.environ["CODEX_WP_GITLEAKS"] = str(slow)
        rc, out, meta = self.run_locked(scan_timeout=1)
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists(), "the worker must not start")
        self.assertTrue(meta["secret_scan"]["timed_out"])
        self.assertEqual(meta["scan_timeout_s"], 1)
        self.assertIn("codex-wp done", out)
        self.assertIn("--scan-timeout 2", out)  # double it: a finished scan is cached, so only the first run waits
        self.assertNotIn("gitleaks:allow", out)  # nothing was found, so false-positive advice would mislead

    def test_noted_lines_are_capped_and_deduplicated_but_all_are_recorded(self):
        lines = "".join(f"DB{i}=postgres://postgres:postgres@127.0.0.1:5432/t{i}\n" for i in range(7))  # gitleaks:allow
        pair = "PAIR=postgres://a:a@localhost/x postgres://a:a@localhost/y\n"  # gitleaks:allow
        self.commit_file("test.env", lines + pair)
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PASS)
        shown = [ln for ln in out.splitlines() if ln.startswith("SECRETS noted (not blocking)")]
        self.assertEqual(cw.NOTED_SHOWN, 5)
        self.assertEqual(len(shown), 5)
        self.assertEqual(len(set(shown)), 5)  # the pair on line 8 is one line, not two
        self.assertIn("SECRETS noted: 3 more not shown", out)  # 8 distinct lines, 5 shown
        self.assertEqual(len(meta["secret_scan"]["noted"]), 9)  # the record keeps every hit

    def test_blocking_lines_are_never_capped(self):
        text = "".join(f"K{i}=postgres://app:{SECRET}@db{i}.internal/x\n" for i in range(7))  # gitleaks:allow
        self.commit_file("config.txt", text)
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertEqual(len([ln for ln in out.splitlines() if ln.startswith("SECRETS blocked:")]), 7)
        self.assertNotIn(SECRET, out)

    # 0.1.7: the known-leaked list

    def test_a_known_leaked_value_blocks_and_names_its_label(self):
        cw.STATE_DIR.mkdir(parents=True, exist_ok=True)
        (cw.STATE_DIR / "leaked-sha12.txt").write_text(f"{h12(LEAKED)} minio-root\n")
        self.commit_file("settings.js", f"MINIO_ROOT_PASSWORD=mock_{LEAKED}\n")
        rc, out, meta = self.run_locked(setup="touch SETUP_RAN")
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists(), "the worker must not start")
        self.assertIn("known-leaked", out)
        self.assertIn("minio-root", out)
        self.assertIn("cannot be allowed by a marker", out)
        self.assertNotIn("A false positive", out)  # no marker advice when every hit is a known-leaked value
        self.assertNotIn(LEAKED, out)
        self.assertNotIn(LEAKED, json.dumps(meta))

    def test_a_broken_leaked_list_fails_closed(self):
        cw.STATE_DIR.mkdir(parents=True, exist_ok=True)
        (cw.STATE_DIR / "leaked-sha12.txt").write_text("not-a-hash\n")
        rc, out, meta = self.run_locked()
        self.assertEqual(rc, cw.EXIT_PRECONDITION)
        self.assertFalse(self.mark.exists())
        self.assertIn("leaked", meta["secret_scan"]["error"])


if __name__ == "__main__":
    unittest.main()
