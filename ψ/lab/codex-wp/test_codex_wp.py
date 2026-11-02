"""Unit tests for codex_wp.py. Offline: no Codex call, no network. Run:

    python3 -m unittest -q test_codex_wp        (from this directory)

Every test here encodes something that went wrong, or nearly did, on 2026-11-02 / 2026-10-07:
  - review looked at the working tree, the worker had already committed -> diff must be base..HEAD
  - the worker's `git add -A` committed __pycache__ -> junk and ownership are checked per path
  - an exit code of 0 hid a dead login -> success needs turn.completed in the event log
  - the quota is a weekly window with no credits -> pace the burst, hard stop near the cap
"""
import json
import os
import subprocess
import sys
import tempfile
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


if __name__ == "__main__":
    unittest.main()
