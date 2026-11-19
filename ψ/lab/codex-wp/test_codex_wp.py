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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codex_wp as cw  # noqa: E402

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

    def test_a_scan_that_runs_too_long_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            gl, _ = fake_gitleaks(d, 0, sleep=5)
            self.assertEqual(cw.run_gitleaks(Path(d), str(gl), timeout=1).status, "error")

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


class Cli014(unittest.TestCase):
    def test_version(self):
        self.assertEqual(cw.VERSION, "0.1.4")

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
            old_state, old_check = cw.STATE_DIR, cw.seat_check
            cw.STATE_DIR = Path(d, "state")
            calls = []

            def seat(**kw):
                calls.append(kw)
                return (cw.EXIT_PASS, []) if len(calls) == 1 else (cw.EXIT_HOLD, ["quota HOLD"])

            cw.seat_check = seat
            held = [cw.acquire_slot(cw.STATE_DIR / "slots", cw.MAX_SLOTS) for _ in range(cw.MAX_SLOTS)]
            timer = threading.Timer(0.3, lambda: os.close(held.pop(0)[0]))  # a run finishes during the wait
            try:
                repo = make_repo(d)
                wp = Path(d, "wp.md")
                wp.write_text(WP_TEXT)
                timer.start()
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = cw.main(["run", str(wp), "--repo", str(repo), "--wait", "1"])
                timer.join()
                self.assertEqual(rc, cw.EXIT_HOLD)
                self.assertEqual(len(calls), 2)
                fd, _ = cw.acquire_slot(cw.STATE_DIR / "slots", cw.MAX_SLOTS)  # the slot was given back
                os.close(fd)
            finally:
                timer.cancel()
                for fd, _ in held:
                    os.close(fd)
                cw.STATE_DIR, cw.seat_check = old_state, old_check

    def test_readme_documents_0_1_4(self):
        text = Path(__file__).with_name("README.md").read_text()
        for needle in ("--wait", "--no-secret-scan", "not run by the tool", "outside the worktree"):
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


class RunFlow(unittest.TestCase):
    """_run_locked end to end with a fake Codex and a fake gitleaks: no network, no quota."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.repo = make_repo(self.d)
        self.mark = self.d / "worker-started"
        self.old_state = cw.STATE_DIR
        cw.STATE_DIR = self.d / "state"
        self.old_env = {k: os.environ.get(k) for k in ("CODEX_WP_BIN", "CODEX_WP_GITLEAKS", "CODEX_HOME")}
        os.environ["CODEX_HOME"] = str(self.d / "codex-home")
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
                    no_secret_scan=None)
        args.update(kw)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cw._run_locked(argparse.Namespace(**args), cw.parse_wp(wp_text), self.repo, 1)
        run_dir = next((cw.STATE_DIR / "runs").iterdir())
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


if __name__ == "__main__":
    unittest.main()
