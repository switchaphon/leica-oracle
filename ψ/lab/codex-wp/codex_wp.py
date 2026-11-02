#!/usr/bin/env python3
"""codex-wp: hand one work package (WP) to a Codex worker, then check the result mechanically.

Roles. The lead (an Opus oracle) designs, writes the WP, READS THE DIFF and decides.
This tool never judges the work. It only does what a script can prove:
  seat     login is valid, the weekly quota is on pace, a slot is free
  worker   runs in its own git worktree, sandboxed (workspace-write, never a bypass flag)
  log      the event stream shows turn.completed (an exit code alone proved nothing on 2026-10-07)
  changes  every changed path is inside "Files owned"; no junk was committed (checked against base..HEAD)

Commands: check | run | follow | verify | review | status | done | selftest      (codex-wp <command> -h)
Exit codes: 0 pass/go | 2 usage | 10 HOLD (over pace) | 11 BUSY | 12 UNAVAILABLE | 14 PRECONDITION
            20 REVISE | 30 FAIL
HOLD and UNAVAILABLE mean: do not pretend. Wait, or fall back to a Claude subagent labelled FALLBACK.
"""
from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as dt
import fcntl
import json
import os
import re
import shutil  # noqa: F401  (shutil.which is used in codex_bin)
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

VERSION = "0.1.2"
DEFAULT_MODEL = os.environ.get("CODEX_WP_MODEL", "gpt-5.6-sol")
STATE_DIR = Path(os.environ.get("CODEX_WP_HOME", str(Path.home() / ".codex-wp")))
MAX_SLOTS = int(os.environ.get("CODEX_WP_SLOTS", "3"))
PACE_SLACK = 10.0  # percentage points a long window may run ahead of a straight line
PACE_CAP = 85.0    # above this: HOLD, whatever the clock says
HARD_STOP = 90.0   # at or above this: FALLBACK
DEFAULT_TIMEOUT_S = 40 * 60
SELFTEST_FILE = STATE_DIR / "selftest.json"
SELFTEST_STALE_S = 3 * 86400  # a passing selftest older than this is reported as stale

EXIT_PASS, EXIT_USAGE, EXIT_HOLD, EXIT_BUSY, EXIT_UNAVAILABLE = 0, 2, 10, 11, 12
EXIT_PRECONDITION, EXIT_REVISE, EXIT_FAIL = 14, 20, 30

PREAMBLE = """\
You are a Codex worker. A lead dispatched this work package and will read your diff.
These rules apply to every work package and win over AGENTS.md where they conflict:
1. Work only inside this git worktree. Edit only the paths listed under "Files owned".
2. Do NOT commit. Do NOT run `git add -A` or `git add .`. The lead stages and commits owned files.
3. No network is available. If a step needs it, stop and say so. Do not work around it.
4. Run the "Verify with" commands and put their full output in your final report.
5. If any command fails, report the exact output. Never hide or work around a failure.
6. Leave no generated files behind (caches, build output, logs) unless they are listed under "Files owned".
Otherwise follow AGENTS.md in this repo if there is one.
Final report: files changed, key decisions, verify output, unresolved items.
"""


def compose_prompt(wp_text: str) -> str:
    return PREAMBLE + "\n---\n\n" + wp_text


# --------------------------------------------------------------------------- work package

class WPError(ValueError):
    """The WP cannot be dispatched as written."""


@dataclasses.dataclass
class WP:
    title: str
    owned: list
    verify: list
    text: str


_KEY = re.compile(r"^\s*[-*]\s*\**\s*(files owned|verify with)\s*\**\s*:\s*\**\s*(.*)$", re.I)
_SUB = re.compile(r"^\s{2,}[-*]\s+(.*)$")
_HEAD = re.compile(r"^\s*#{1,6}\s*(?:WP-?\d*\s*[:.\-]\s*)?(.+?)\s*$")


def _unwrap(v: str) -> str:
    v = v.strip()
    if len(v) > 1 and v.startswith("`") and v.endswith("`") and v.count("`") == 2:
        v = v[1:-1].strip()
    return v


def parse_wp(text: str) -> WP:
    lines = text.splitlines()
    title = "wp"
    for ln in lines:
        m = _HEAD.match(ln)
        if m:
            title = m.group(1)
            break
    fields = {"files owned": [], "verify with": []}
    i = 0
    while i < len(lines):
        m = _KEY.match(lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1).lower(), m.group(2).strip()
        if val:
            fields[key].append(val)
        j = i + 1
        while j < len(lines):
            sub = _SUB.match(lines[j])
            if not sub:
                break
            fields[key].append(sub.group(1).strip())
            j += 1
        i = j
    owned = []
    for v in fields["files owned"]:
        for part in re.split(r"[;,]", v):
            p = _unwrap(part)
            if re.search(r"\s(#|\()", p):
                raise WPError(f"'Files owned' item {p!r} looks like a path followed by a note. "
                              "Put notes on their own line: a note glued to a path fails every ownership check.")
            if p:
                owned.append(p)
    verify = [c for c in (_unwrap(v) for v in fields["verify with"]) if c]
    if not owned:
        raise WPError("the WP has no 'Files owned:' line. Refusing to dispatch without disjoint file ownership.")
    return WP(title, owned, verify, text)


# --------------------------------------------------------------------------- ownership

def _glob_re(pat: str):
    pat = pat.strip()
    if pat.startswith("./"):
        pat = pat[2:]
    if pat.endswith("/"):
        pat += "**"
    out, i = [], 0
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if pat[i:i + 2] == "**":
                i += 2
                if pat[i:i + 1] == "/":
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def match_owned(path: str, patterns) -> bool:
    if path.startswith("./"):
        path = path[2:]
    return any(_glob_re(p).match(path) for p in patterns if p.strip())


_JUNK_SEGMENTS = {"__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".omx", ".next", ".turbo"}
_JUNK_SUFFIXES = (".pyc", ".pyo", ".log", ".swp")


def is_junk(path: str) -> bool:
    parts = path.split("/")
    if any(p in _JUNK_SEGMENTS for p in parts):
        return True
    base = parts[-1]
    if base == ".DS_Store" or base.endswith(_JUNK_SUFFIXES):
        return True
    if base == ".env" or (base.startswith(".env.") and not base.endswith((".example", ".sample", ".template"))):
        return True
    return False


@dataclasses.dataclass
class Assessment:
    owned_changed: list
    violations: list
    committed_junk: list
    dirty_junk: list

    @property
    def clean(self) -> bool:
        return bool(self.owned_changed) and not self.violations and not self.committed_junk


def assess_changes(committed, dirty, owned) -> Assessment:
    cset = set(committed)
    owned_changed, violations, committed_junk, dirty_junk = [], [], [], []
    for p in sorted(cset | set(dirty)):
        if is_junk(p):
            (committed_junk if p in cset else dirty_junk).append(p)
        elif match_owned(p, owned):
            owned_changed.append(p)
        else:
            violations.append(p)
    return Assessment(owned_changed, violations, committed_junk, dirty_junk)


def decide(worker_failures, a: Assessment):
    if worker_failures:
        return "FAIL", list(worker_failures)
    reasons = []
    if not a.owned_changed:
        reasons.append("no file under 'Files owned' changed")
    if a.violations:
        reasons.append("changed files outside 'Files owned': " + ", ".join(a.violations))
    if a.committed_junk:
        reasons.append("junk was committed: " + ", ".join(a.committed_junk))
    return ("REVISE", reasons) if reasons else ("PASS", [])


# --------------------------------------------------------------------------- git

class GitError(RuntimeError):
    pass


def git(args, cwd, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise GitError("git " + " ".join(args) + ": " + (r.stderr or r.stdout).strip())
    return r


def parse_porcelain_z(out: str) -> list:
    toks = out.split("\0")
    paths, i = [], 0
    while i < len(toks):
        t = toks[i]
        if not t:
            i += 1
            continue
        xy, path = t[:2], t[3:]
        paths.append(path)
        if xy[0] in "RC":  # a rename or copy carries the original path as the next token
            i += 1
        i += 1
    return paths


def dirty_paths(wt) -> list:
    return parse_porcelain_z(git(["status", "--porcelain=v1", "-z", "--untracked-files=all"], wt).stdout)


def committed_paths(wt, base) -> list:
    out = git(["diff", "--name-only", "-z", f"{base}..HEAD"], wt).stdout
    return [p for p in out.split("\0") if p]


def make_worktree(repo, base_ref, branch, dest) -> str:
    sha = git(["rev-parse", "--verify", f"{base_ref}^{{commit}}"], repo).stdout.strip()
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    git(["worktree", "add", "-q", "-b", branch, str(dest), sha], repo)
    return sha


def commit_owned(wt, owned, message):
    """Stage and commit ONLY dirty paths that are owned and not junk. Returns the short sha or None."""
    todo = [p for p in dirty_paths(wt) if not is_junk(p) and match_owned(p, owned)]
    if not todo:
        return None
    git(["--literal-pathspecs", "add", "-A", "--", *todo], wt)
    ident = []
    if not git(["config", "user.email"], wt, check=False).stdout.strip():
        ident = ["-c", "user.name=codex-wp", "-c", "user.email=codex-wp@localhost"]
    git([*ident, "--literal-pathspecs", "commit", "-q", "-m", message, "--only", "--", *todo], wt)
    return git(["rev-parse", "--short", "HEAD"], wt).stdout.strip()


def run_commands(cmds, cwd, timeout=900):
    out = []
    for c in cmds:
        try:
            # shell=True on purpose: these strings are the lead's own "Verify with:" lines (trusted, and they
            # need &&, pipes and env prefixes). Never build one from worker output or any file the worker wrote.
            r = subprocess.run(c, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-25:])
            out.append((c, r.returncode, tail))
        except subprocess.TimeoutExpired:
            out.append((c, 124, f"timeout after {timeout}s"))
    return out


# --------------------------------------------------------------------------- quota

@dataclasses.dataclass
class Verdict:
    kind: str
    reason: str
    used: float | None = None
    allowed: float | None = None
    elapsed: float | None = None
    resets_at: float | None = None


_RANK = {"GO": 0, "HOLD": 1, "FALLBACK": 2}


def _window_verdict(name, w, now, cap, hard, slack) -> Verdict:
    used = float(w.get("used_percent") or 0.0)
    minutes = float(w.get("window_minutes") or 0.0)
    resets = w.get("resets_at")
    resets = float(resets) if resets is not None else None
    if resets is not None and now >= resets:
        return Verdict("GO", f"{name} window rolled over since the snapshot (stale, treated as fresh)",
                       0.0, None, 0.0, resets)
    elapsed = None
    if minutes and resets is not None:
        span = minutes * 60.0
        elapsed = min(max((now - (resets - span)) / span, 0.0), 1.0) * 100.0
    if used >= hard:
        return Verdict("FALLBACK", f"{name} window at {used:.1f}% (hard stop {hard:.0f}%)", used, None, elapsed, resets)
    allowed = cap
    if elapsed is not None and minutes >= 1440:  # only long windows are paced against the clock
        allowed = min(cap, elapsed + slack)
    if used > allowed:
        return Verdict("HOLD", f"{name} window used {used:.1f}% > allowed {allowed:.1f}%", used, allowed, elapsed, resets)
    return Verdict("GO", f"{name} window used {used:.1f}% <= allowed {allowed:.1f}%", used, allowed, elapsed, resets)


def pace_verdict(rl, now, cap=PACE_CAP, hard=HARD_STOP, slack=PACE_SLACK) -> Verdict:
    if not rl:
        return Verdict("UNKNOWN", "no rate-limit snapshot yet")
    reached = rl.get("rate_limit_reached_type")
    if reached:
        return Verdict("FALLBACK", f"limit reached ({reached})")
    best = None
    for name in ("primary", "secondary"):
        w = rl.get(name)
        if not isinstance(w, dict):
            continue
        v = _window_verdict(name, w, now, cap, hard, slack)
        if (best is None or _RANK[v.kind] > _RANK[best.kind]
                or (_RANK[v.kind] == _RANK[best.kind] and (v.used or 0) > (best.used or 0))):
            best = v
    return best or Verdict("UNKNOWN", "snapshot has no windows")


@dataclasses.dataclass
class Snapshot:
    ts: float
    rate_limits: dict
    source: Path


def parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def find_rollouts(homes, limit=8) -> list:
    files = []
    for h in homes:
        root = Path(h) / "sessions"
        if root.is_dir():
            files += list(root.glob("*/*/*/rollout-*.jsonl"))
    files.sort(key=_mtime, reverse=True)
    return files[:limit]


def find_rollout_for_thread(homes, thread_id):
    if not thread_id:
        return None
    for h in homes:
        root = Path(h) / "sessions"
        if root.is_dir():
            for f in root.glob(f"*/*/*/rollout-*{thread_id}*.jsonl"):
                return f
    return None


def rate_limits_from_rollout(path: Path, tail_bytes=1_000_000):
    try:
        size = path.stat().st_size
        with open(path, "rb") as f:
            if size > tail_bytes:
                f.seek(size - tail_bytes)
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    last = None
    for line in data.splitlines():
        if '"token_count"' not in line:
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        p = o.get("payload") if isinstance(o, dict) else None
        if isinstance(p, dict) and p.get("type") == "token_count" and p.get("rate_limits"):
            last = (o.get("timestamp"), p["rate_limits"])
    return last


def latest_snapshot(homes):
    for f in find_rollouts(homes):
        r = rate_limits_from_rollout(f)
        if r:
            return Snapshot(parse_ts(r[0]) or _mtime(f), r[1], f)
    return None


# --------------------------------------------------------------------------- worker process

@dataclasses.dataclass
class EventSummary:
    completed: bool
    failed: bool
    thread_id: str | None
    usage: dict | None
    errors: list


def summarize_events(text: str) -> EventSummary:
    s = EventSummary(False, False, None, None, [])
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        t = o.get("type")
        if t == "thread.started":
            s.thread_id = o.get("thread_id")
        elif t == "turn.completed":
            s.completed = True
            s.usage = o.get("usage")
        elif t in ("turn.failed", "error"):
            err = o.get("error")
            msg = err.get("message") if isinstance(err, dict) else err
            s.errors.append(str(msg or o.get("message") or "")[:300])
            if t == "turn.failed":
                s.failed = True
    return s


def build_exec_argv(*, codex_bin, worktree, model, sandbox, report_path, effort=None, skip_git_check=False):
    if sandbox not in ("read-only", "workspace-write"):
        raise ValueError(f"sandbox must be read-only or workspace-write, never {sandbox!r}")
    argv = [str(codex_bin), "exec", "-s", sandbox, "-C", str(worktree), "-m", model,
            "--json", "--ignore-user-config", "-o", str(report_path),
            "-c", "shell_environment_policy.inherit=core"]
    if skip_git_check:
        argv.append("--skip-git-repo-check")
    if effort:
        argv += ["-c", f'model_reasoning_effort="{effort}"']
    argv.append("-")  # the prompt arrives on stdin
    return argv


def kill_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


# --------------------------------------------------------------------------- slots

class SlotBusy(RuntimeError):
    pass


def acquire_slot(directory, n):
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        fd = os.open(str(d / f"slot-{i}.lock"), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            continue
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()} {int(time.time())}\n".encode())
        return fd, i
    raise SlotBusy(f"all {n} slots busy")


def busy_slots(directory, n) -> int:
    busy = 0
    for i in range(1, n + 1):
        p = Path(directory) / f"slot-{i}.lock"
        if not p.exists():
            continue
        fd = os.open(str(p), os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            busy += 1
        finally:
            os.close(fd)
    return busy


# --------------------------------------------------------------------------- seat

def codex_bin():
    return os.environ.get("CODEX_WP_BIN") or shutil.which("codex")


def codex_homes() -> list:
    env = os.environ.get("CODEX_HOME")
    homes = [Path(env) if env else Path.home() / ".codex"]
    team = Path.home() / ".codex-team"
    if team.is_dir():
        homes += sorted(p for p in team.iterdir() if p.is_dir())
    return homes


def plan_type():
    try:
        d = json.loads((codex_homes()[0] / "auth.json").read_text())
        seg = (d.get("tokens") or {})["id_token"].split(".")[1]
        seg += "=" * (-len(seg) % 4)
        claims = json.loads(base64.urlsafe_b64decode(seg))
        return (claims.get("https://api.openai.com/auth") or {}).get("chatgpt_plan_type")
    except Exception:  # noqa: BLE001  (a missing or odd auth.json only means "plan unknown")
        return None


def login_status(binary):
    try:
        r = subprocess.run([binary, "login", "status"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"codex login status could not run: {e}"
    text = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode == 0, (text[0] if text else "")


def read_selftest_record(path):
    """The record of the last selftest, or None when it is missing or unreadable."""
    try:
        d = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) else None


def write_selftest_record(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(record, indent=2))
    os.replace(tmp, p)


def selftest_status(record, codex_version, model, now):
    """A pass proves only the Codex version and model it ran on. Says whether it still covers today's seat."""
    if not record:
        return "NONE", f"no selftest on record for {codex_version}: run `codex-wp selftest` before the first WP"
    if record.get("result") != "PASS":
        return "FAILED", f"the last selftest FAILED on {record.get('codex_version')}: do not dispatch until it passes"
    if record.get("codex_version") != codex_version or record.get("model") != model:
        return "DIFFERENT", (f"the last passing selftest was on {record.get('codex_version')} / {record.get('model')}, "
                             f"this is {codex_version} / {model}: run `codex-wp selftest`")
    age = now - float(record.get("ts") or 0)
    if age > SELFTEST_STALE_S:
        return "STALE", f"selftest PASS on {codex_version} but {int(age / 86400)} days ago: re-run `codex-wp selftest`"
    return "OK", f"PASS on {codex_version} ({int(age / 3600)}h ago)"


def fmt_local(ts):
    return time.strftime("%a %d %b %H:%M", time.localtime(ts)) if ts else "?"


def run_probe(binary, model):
    with tempfile.TemporaryDirectory(prefix="codex-wp-probe-") as d:
        out = Path(d, "o.txt")
        argv = build_exec_argv(codex_bin=binary, worktree=d, model=model, sandbox="read-only",
                               report_path=out, skip_git_check=True)
        try:
            r = subprocess.run(argv, input="Reply with exactly: PROBE_OK", capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, str(e)
        s = summarize_events(r.stdout)
        text = out.read_text() if out.exists() else ""
        good = s.completed and "PROBE_OK" in text
        used = (s.usage or {}).get("input_tokens")
        detail = f"{'completed' if s.completed else 'no turn.completed'}, {used} input tokens"
        if not good:
            detail += f"; reply={text.strip()[:80]!r} errors={s.errors[:1]}"
        return good, detail


def seat_check(probe=False, now=None, model=DEFAULT_MODEL):
    now = time.time() if now is None else now
    binary = codex_bin()
    if not binary:
        return EXIT_UNAVAILABLE, ["UNAVAILABLE: no codex binary on PATH (set CODEX_WP_BIN). "
                                  "Fall back to a Claude subagent labelled FALLBACK."]
    ver = subprocess.run([binary, "--version"], capture_output=True, text=True).stdout.strip()
    ok, msg = login_status(binary)
    plan = plan_type()
    lines = [f"codex   {binary} ({ver})",
             f"login   {msg or 'unknown'}" + (f" | plan {plan}" if plan else ""),
             f"model   {model} (pinned)"]
    st_kind, st_text = selftest_status(read_selftest_record(SELFTEST_FILE), ver, model, now)
    lines.append(f"selftest {st_text}" if st_kind == "OK" else f"selftest WARN ({st_kind}) {st_text}")
    if not ok:
        lines.append("UNAVAILABLE: not logged in. Run `codex login`. Do not call Codex dead until `codex-wp selftest` fails.")
        return EXIT_UNAVAILABLE, lines
    if probe:
        good, detail = run_probe(binary, model)
        lines.append(f"probe   {'ok' if good else 'FAILED'}: {detail}")
        if not good:
            lines.append("UNAVAILABLE: the probe call failed. Fall back to a Claude subagent labelled FALLBACK.")
            return EXIT_UNAVAILABLE, lines
    lines.append(f"slots   {busy_slots(STATE_DIR / 'slots', MAX_SLOTS)}/{MAX_SLOTS} busy")
    snap = latest_snapshot(codex_homes())
    v = pace_verdict(snap.rate_limits if snap else None, now)
    if snap:
        lines.append(f"quota   {v.reason} | snapshot {int((now - snap.ts) / 60)}m old")
        if v.elapsed is not None:
            lines.append(f"        window {v.elapsed:.1f}% elapsed, resets {fmt_local(v.resets_at)}")
    else:
        lines.append("quota   no snapshot yet (run `codex-wp check --probe`)")
    lines.append(f"verdict {v.kind}")
    code = {"GO": EXIT_PASS, "UNKNOWN": EXIT_PASS, "HOLD": EXIT_HOLD, "FALLBACK": EXIT_UNAVAILABLE}[v.kind]
    if v.kind == "HOLD":
        lines.append('HOLD: ahead of the weekly pace. Wait, send only urgent WPs with --force-pace "reason", '
                     "or use a FALLBACK subagent.")
    if v.kind == "FALLBACK":
        lines.append("UNAVAILABLE: quota exhausted or at the hard stop. Fall back to a Claude subagent "
                     "labelled FALLBACK, or wait for the reset.")
    return code, lines


# --------------------------------------------------------------------------- commands

def new_run_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:24] or "wp"
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{slug}-{os.urandom(2).hex()}"


def resolve_run_dir(run_id: str) -> Path:
    """A run directory by exact id or by unique prefix. Does not need meta.json (a run may have only just started)."""
    root = STATE_DIR / "runs"
    cand = root / run_id
    if not cand.is_dir():
        matches = sorted(p for p in root.glob(run_id + "*") if p.is_dir()) if root.is_dir() else []
        if len(matches) != 1:
            raise WPError(f"no unique run matching {run_id!r} under {root}")
        cand = matches[0]
    return cand


def newest_run_dir():
    root = STATE_DIR / "runs"
    dirs = sorted(p for p in root.glob("*") if p.is_dir()) if root.is_dir() else []
    return dirs[-1] if dirs else None


def load_meta(run_id: str):
    cand = resolve_run_dir(run_id)
    return json.loads((cand / "meta.json").read_text()), cand


def run_setup(cmd, cwd, timeout=1800):
    """Run the lead's --setup command (a dependency install, a node_modules link). Returns (ok, detail)."""
    try:
        # shell=True on purpose: --setup is typed by the lead (e.g. a dependency install), never by the worker.
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"setup timed out after {timeout}s"
    if r.returncode != 0:
        return False, f"setup failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[-200:]}"
    return True, ""


def base_check(repo, base_ref, verify_cmds, run_id, setup=None):
    """TDD precondition: at least one verify command must FAIL on the base commit. It runs in the same environment the
    worker gets (so --setup runs here too; without it a verify that needs node_modules fails for the wrong reason and
    the red is fake) and says why it failed, so the lead can judge whether it is the right red."""
    tmp = STATE_DIR / "worktrees" / f"{Path(repo).name}-{run_id}-basecheck"
    sha = git(["rev-parse", "--verify", f"{base_ref}^{{commit}}"], repo).stdout.strip()
    tmp.parent.mkdir(parents=True, exist_ok=True)
    git(["worktree", "add", "-q", "--detach", str(tmp), sha], repo)
    try:
        if setup:
            ok_setup, detail_setup = run_setup(setup, tmp)
            if not ok_setup:
                return False, (f"{detail_setup}; the base worktree needs the same setup as the worker, "
                               "so a red here cannot be trusted")
        results = run_commands(verify_cmds, tmp)
    finally:
        git(["worktree", "remove", "--force", str(tmp)], repo, check=False)
    failing = [(c, rc, tail) for c, rc, tail in results if rc != 0]
    if not failing:
        return False, ("every Verify command already PASSES on the base commit, so passing afterwards proves "
                       "nothing. Write the test so it fails first.")
    last = [ln for ln in failing[0][2].splitlines() if ln.strip()]
    why = _clip(last[-1], 110) if last else f"exit {failing[0][1]}"
    return True, (f"{len(failing)} of {len(results)} verify command(s) fail on base, as they should; "
                  f"first failure: {why}")


def only_links_and_junk(wt) -> bool:
    """True when everything git calls dirty in the worktree is a symlink or generated junk: nothing worth keeping."""
    return all(is_junk(p) or (Path(wt) / p).is_symlink() for p in dirty_paths(wt))


def _clip(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 3] + "..."


_SHELL_WRAP = re.compile(r'^(?:/bin/)?(?:zsh|bash|sh) -lc "(.*)"$', re.S)


def format_event(o, strip=None) -> list:
    """One codex exec --json event as zero or more short lines for a human watching a tmux pane."""
    t = o.get("type")
    item = o.get("item") or {}
    kind = item.get("type")
    if t == "item.started" and kind == "command_execution":
        cmd = str(item.get("command") or "")
        m = _SHELL_WRAP.match(cmd)
        return ["$ " + _clip(m.group(1) if m else cmd, 146)]
    if t == "item.completed" and kind == "command_execution":
        code = item.get("exit_code")
        if code is None:
            return []
        if code == 0:
            return ["  exit 0"]
        last = [ln for ln in str(item.get("aggregated_output") or "").splitlines() if ln.strip()]
        return [f"  exit {code}" + (f": {_clip(last[-1], 110)}" if last else "")]
    if t == "item.completed" and kind == "agent_message":
        return ["agent: " + _clip(item.get("text") or "", 300)]
    if t == "item.completed" and kind == "file_change":
        lines = []
        for c in item.get("changes") or []:
            if isinstance(c, dict):
                path = str(c.get("path") or "?")
                if strip and path.startswith(strip):
                    path = path[len(strip):]
                lines.append(f"edit {c.get('kind') or c.get('type') or '?'} {path}")
            else:
                lines.append("edit " + _clip(c, 120))
        return lines
    if t == "turn.completed":
        u = o.get("usage") or {}
        return [f"turn completed: tokens in {u.get('input_tokens')} (cached {u.get('cached_input_tokens')}) "
                f"out {u.get('output_tokens')}"]
    if t in ("turn.failed", "error"):
        err = o.get("error")
        msg = err.get("message") if isinstance(err, dict) else err
        return ["ERROR: " + _clip(msg or o.get("message") or "", 200)]
    return []


def follow_lines(path, is_finished, poll=0.4):
    """Yield the complete lines of a file that is still being written, never a half-written one. Ends once
    is_finished() is true AND everything written before that moment has been read."""
    pos, buf = 0, b""
    while True:
        done = is_finished()  # sampled BEFORE the read: whatever was written before it finished is read below
        try:
            with open(path, "rb") as f:
                f.seek(pos)
                chunk = f.read()
                pos += len(chunk)
        except OSError:
            chunk = b""
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if line.strip():
                yield line.decode("utf-8", "replace")
        if done:
            return
        time.sleep(poll)


FINAL_STATUSES = {"PASS", "REVISE", "FAIL", "PRECONDITION"}


def cmd_follow(a):
    """Read-only live view of a run: open it in a tmux pane. Works while the lead runs the WP in the background."""
    run_dir = resolve_run_dir(a.run) if a.run else newest_run_dir()
    if run_dir is None:
        print("no runs yet")
        return EXIT_USAGE
    meta_path = run_dir / "meta.json"

    def read_meta():
        try:
            return json.loads(meta_path.read_text())
        except (OSError, ValueError):
            return {}

    finished = (lambda: True) if a.no_wait else (lambda: read_meta().get("status") in FINAL_STATUSES)
    strip = (read_meta().get("worktree") or "") + "/" if read_meta().get("worktree") else None
    print(f"following {run_dir.name}   (read-only, Ctrl-C to stop)", flush=True)
    for raw in follow_lines(run_dir / "events.jsonl", finished):
        try:
            ev = json.loads(raw)
        except ValueError:
            continue
        for line in format_event(ev, strip=strip):
            print(f"{time.strftime('%H:%M:%S')}  {line}", flush=True)
    m = read_meta()
    print(f"-- {m.get('status') or 'still running'}: {run_dir.name}"
          + (f"  ({'; '.join(m.get('reasons') or [])})" if m.get("reasons") else ""))
    return EXIT_PASS


def cmd_check(a):
    code, lines = seat_check(probe=a.probe, model=a.model)
    print("\n".join(lines))
    return code


def cmd_run(a):
    try:
        wp = parse_wp(Path(a.wp).read_text())
    except (OSError, WPError) as e:
        print(f"USAGE: {e}", file=sys.stderr)
        return EXIT_USAGE
    repo_arg = Path(a.repo).resolve()
    if not repo_arg.is_dir():
        print(f"USAGE: {repo_arg} is not a directory", file=sys.stderr)
        return EXIT_USAGE
    top = git(["rev-parse", "--show-toplevel"], repo_arg, check=False)
    if top.returncode != 0:
        print(f"USAGE: {repo_arg} is not inside a git repository", file=sys.stderr)
        return EXIT_USAGE
    repo = Path(top.stdout.strip())
    code, lines = seat_check(model=a.model)
    print("\n".join(lines))
    if code == EXIT_HOLD and a.force_pace:
        print(f"PACE OVERRIDE by the lead: {a.force_pace}")
        code = EXIT_PASS
    if code != EXIT_PASS:
        return code
    try:
        slot_fd, slot = acquire_slot(STATE_DIR / "slots", MAX_SLOTS)
    except SlotBusy:
        print(f"BUSY: all {MAX_SLOTS} Codex slots are in use. Wait for one to finish, or fall back.")
        return EXIT_BUSY
    try:
        return _run_locked(a, wp, repo, slot)
    finally:
        os.close(slot_fd)


def _run_locked(a, wp, repo, slot):
    run_id = new_run_id(wp.title)
    run_dir = STATE_DIR / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "wp.md").write_text(wp.text)
    meta = {"run_id": run_id, "title": wp.title, "repo": str(repo), "owned": wp.owned,
            "verify_cmds": wp.verify, "model": a.model, "started": time.time(),
            "tool_version": VERSION, "status": "STARTING"}

    def save():
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))

    if git(["status", "--porcelain", "--untracked-files=no"], repo).stdout.strip():
        print(f"WARN    uncommitted tracked changes in {repo}: the worker is cut from {a.base} and will not see them")
    if a.tdd:
        if not wp.verify:
            print("USAGE: --tdd needs a 'Verify with:' line in the WP", file=sys.stderr)
            return EXIT_USAGE
        ok, detail = base_check(repo, a.base, wp.verify, run_id, setup=a.setup)
        meta["tdd"] = {"ok": ok, "detail": detail}
        print(("TDD     " if ok else "TDD CHECK FAILED  ") + detail)
        if not ok:
            meta["status"] = "PRECONDITION"
            save()
            return EXIT_PRECONDITION

    branch = f"wp/{run_id}"
    wt = STATE_DIR / "worktrees" / f"{repo.name}-{run_id}"
    base_sha = make_worktree(repo, a.base, branch, wt)
    meta.update(branch=branch, worktree=str(wt), base=base_sha)
    save()
    print(f"RUN     {run_id}\n  dir      {run_dir}\n  worktree {wt}\n"
          f"  branch   {branch} (base {base_sha[:9]})\n  slot     {slot}/{MAX_SLOTS}", flush=True)

    failures = []
    ran = False
    if a.setup:
        ok_setup, detail_setup = run_setup(a.setup, wt)
        if not ok_setup:
            failures.append(detail_setup)

    prompt = compose_prompt(wp.text)
    (run_dir / "prompt.md").write_text(prompt)
    report, events, err = run_dir / "report.md", run_dir / "events.jsonl", run_dir / "stderr.txt"
    t0 = time.time()
    rc = None
    if not failures:
        ran = True
        argv = build_exec_argv(codex_bin=codex_bin(), worktree=wt, model=a.model, sandbox="workspace-write",
                               report_path=report, effort=a.effort)
        with open(events, "w") as fo, open(err, "w") as fe:
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=fo, stderr=fe, text=True,
                                    cwd=str(wt), start_new_session=True)
            try:
                proc.communicate(prompt, timeout=a.timeout)
            except subprocess.TimeoutExpired:
                kill_group(proc)
                failures.append(f"timeout after {a.timeout}s")
        rc = proc.returncode
        if rc not in (0, None) and not failures:
            failures.append(f"codex exit {rc}")
    elapsed = time.time() - t0

    summary = summarize_events(events.read_text(errors="replace") if events.exists() else "")
    if ran:
        if not summary.completed:
            failures.append("no turn.completed in the event log (an exit code alone is not proof)")
        if summary.failed:
            failures.append("turn failed: " + "; ".join(summary.errors[:2]))
        if not (report.exists() and report.read_text(errors="replace").strip()):
            failures.append("empty final report")

    worker_commits = int(git(["rev-list", "--count", f"{base_sha}..HEAD"], wt).stdout.strip() or 0)
    wrapper_commit = None
    if not failures:
        wrapper_commit = commit_owned(wt, wp.owned, f"wp: {wp.title}")
    assess = assess_changes(committed_paths(wt, base_sha), dirty_paths(wt), wp.owned)
    status, reasons = decide(failures, assess)

    verify_results = None
    if a.verify_now and wp.verify and status in ("PASS", "REVISE"):
        verify_results = run_commands(wp.verify, wt)
        bad = [c for c, code_, _ in verify_results if code_ != 0]
        if bad:
            status = "REVISE"
            reasons.append("verify failed: " + bad[0])

    after = latest_snapshot(codex_homes())
    quota = pace_verdict(after.rate_limits if after else None, time.time())
    usage = summary.usage or {}
    meta.update(status=status, reasons=reasons, elapsed_s=round(elapsed, 1), worker_exit=rc,
                completed=summary.completed, thread_id=summary.thread_id, usage=usage,
                owned_changed=assess.owned_changed, violations=assess.violations,
                committed_junk=assess.committed_junk, dirty_junk=assess.dirty_junk,
                worker_commits=worker_commits, wrapper_commit=wrapper_commit,
                quota=dataclasses.asdict(quota), verify_results=verify_results)
    save()

    out = [f"RESULT  {status}" + (f"  ({'; '.join(reasons)})" if reasons else ""),
           f"  worker   exit {rc} | completed {'yes' if summary.completed else 'NO'} | {elapsed:.0f}s | {a.model} | "
           f"tokens in {usage.get('input_tokens')} (cached {usage.get('cached_input_tokens')}) out {usage.get('output_tokens')}",
           f"  changed  {', '.join(assess.owned_changed) or '(nothing owned changed)'}"]
    if worker_commits:
        out.append(f"  WARN     the worker made {worker_commits} commit(s) despite the rules; read them in the diff")
    if assess.dirty_junk:
        out.append(f"  note     untracked junk left in the worktree (not committed): {', '.join(assess.dirty_junk[:3])}")
    if verify_results:
        out.append("  verify   " + " | ".join(f"{'ok' if c == 0 else 'FAIL'} {cmd}" for cmd, c, _ in verify_results))
    out.append(f"  quota    {quota.kind}: {quota.reason}")
    out.append(f"  next     read the diff: git -C {wt} diff {base_sha[:9]}..HEAD")
    out.append(f"           then: codex-wp verify {run_id}      worker report: {report}")
    print("\n".join(out))
    return {"PASS": EXIT_PASS, "REVISE": EXIT_REVISE, "FAIL": EXIT_FAIL}[status]


def cmd_verify(a):
    meta, run_dir = load_meta(a.run)
    cmds = meta.get("verify_cmds") or []
    if not cmds:
        print("this WP has no 'Verify with:' commands")
        return EXIT_USAGE
    results = run_commands(cmds, Path(meta["worktree"]))
    for cmd, code, tail in results:
        print(f"{'ok  ' if code == 0 else 'FAIL'} [{code}] {cmd}")
        if code != 0 or a.verbose:
            print(textwrap.indent(tail, "       "))
    meta["verify_results"] = [list(r) for r in results]
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
    return EXIT_PASS if all(c == 0 for _, c, _ in results) else EXIT_REVISE


def cmd_review(a):
    meta, _ = load_meta(a.run)
    wt = Path(meta["worktree"])
    assess = assess_changes(committed_paths(wt, meta["base"]), dirty_paths(wt), meta["owned"])
    status, reasons = decide([], assess)
    print(f"REVIEW  {meta['run_id']}: {status}" + (f"  ({'; '.join(reasons)})" if reasons else ""))
    print(f"  owned changed  {', '.join(assess.owned_changed) or '-'}")
    print(f"  violations     {', '.join(assess.violations) or '-'}")
    print(f"  junk committed {', '.join(assess.committed_junk) or '-'} | untracked {', '.join(assess.dirty_junk) or '-'}")
    print(f"  diff           git -C {wt} diff {meta['base'][:9]}..HEAD")
    return EXIT_PASS if status == "PASS" else EXIT_REVISE


def cmd_status(a):
    _, lines = seat_check(model=a.model)
    print("\n".join(lines))
    root = STATE_DIR / "runs"
    metas = sorted(root.glob("*/meta.json"), reverse=True)[: a.limit] if root.is_dir() else []
    print()
    for p in metas:
        try:
            m = json.loads(p.read_text())
        except ValueError:
            continue
        print(f"{m.get('run_id', p.parent.name):<46} {m.get('status', '?'):<12} {str(m.get('elapsed_s', '-')) + 's':<8} {m.get('title', '')}")
    if not metas:
        print("(no runs yet)")
    return EXIT_PASS


def cmd_done(a):
    meta, _ = load_meta(a.run)
    wt, repo = Path(meta["worktree"]), Path(meta["repo"])
    if not wt.exists():
        print("worktree already gone")
        return EXIT_PASS
    r = git(["worktree", "remove", *(["--force"] if a.force else []), str(wt)], repo, check=False)
    note = ""
    if r.returncode != 0 and not a.force and only_links_and_junk(wt):
        # git refuses any untracked content. A symlink (--setup often links node_modules) or generated junk is not work.
        r = git(["worktree", "remove", "--force", str(wt)], repo, check=False)
        note = " (only symlinks and generated junk were untracked there; link targets are untouched)"
    if r.returncode != 0:
        print(f"not removed: {(r.stderr or r.stdout).strip()}\n"
              "read what is in it, then use --force. The branch is kept either way.")
        return EXIT_REVISE
    print(f"worktree removed{note}; branch {meta['branch']} is kept (nothing is deleted)")
    return EXIT_PASS


SELFTEST_WP = """\
## WP-1: selftest implement add()
- Goal: make test_add.py pass.
- Files owned: add.py
- Context: add(a, b) returns the sum of two numbers. Nothing else is needed.
- Constraints: change add.py only.
- Verify with: python3 -m unittest -q test_add
- Report back: files changed, key decisions, verify output, unresolved items.
"""


def cmd_selftest(a):
    """End to end positive control. 'Codex is dead' needs this to FAIL first."""
    d = Path(tempfile.mkdtemp(prefix="codex-wp-selftest-"))
    repo = d / "repo"
    repo.mkdir()

    def sh(*args):
        subprocess.run(args, cwd=str(repo), check=True, capture_output=True)

    sh("git", "init", "-q", "-b", "main")
    sh("git", "config", "user.email", "selftest@example.invalid")
    sh("git", "config", "user.name", "selftest")
    (repo / "AGENTS.md").write_text("# Selftest repo\nEnd every final report with the exact line: SELFTEST-AGENTS-HONORED\n")
    (repo / "add.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    (repo / "test_add.py").write_text(
        "import unittest\nfrom add import add\n\n\nclass T(unittest.TestCase):\n"
        "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n\n"
        "    def test_negative(self):\n        self.assertEqual(add(-1, 1), 0)\n")
    sh("git", "add", "-A")
    sh("git", "commit", "-q", "-m", "base: failing test, stub")
    wp = d / "wp.md"
    wp.write_text(SELFTEST_WP)
    argv = [sys.executable, str(Path(__file__).resolve()), "run", str(wp), "--repo", str(repo),
            "--tdd", "--setup", "true", "--verify-now", "--model", a.model]  # "true" walks the setup path end to end
    print(f"selftest dir: {d}\nrunning: {' '.join(argv)}\n"
          "(spends roughly 150k tokens, a small fraction of one percent of a weekly window)\n", flush=True)
    r = subprocess.run(argv, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT_S)
    print(r.stdout)
    if r.stderr.strip():
        print(r.stderr, file=sys.stderr)

    checks = []  # (name, ok, hard, detail)

    def check(name, ok, hard=True, detail=""):
        checks.append((name, bool(ok), hard, detail))

    check("run exited 0 (PASS)", r.returncode == 0, detail=f"exit {r.returncode}")
    m = re.search(r"^RUN\s+(\S+)", r.stdout, re.M)
    meta = None
    if m:
        try:
            meta, run_dir = load_meta(m.group(1))
        except (WPError, OSError, ValueError):
            meta = None
    if meta:
        report = Path(run_dir) / "report.md"
        check("TDD precondition: verify failed on base", (meta.get("tdd") or {}).get("ok") is True)
        check("event log shows turn.completed", meta.get("completed") is True)
        check("only add.py changed", meta.get("owned_changed") == ["add.py"] and not meta.get("violations"),
              detail=str(meta.get("owned_changed")))
        check("no junk committed", not meta.get("committed_junk"))
        check("verify passed in the worktree",
              bool(meta.get("verify_results")) and all(x[1] == 0 for x in meta["verify_results"]))
        check("AGENTS.md honored under --ignore-user-config",
              report.exists() and "SELFTEST-AGENTS-HONORED" in report.read_text(errors="replace"))
        check("worker followed 'do not commit'", meta.get("worker_commits") == 0, hard=False,
              detail=f"{meta.get('worker_commits')} commit(s)")
        usage = meta.get("usage") or {}
        check(f"token overhead (input {usage.get('input_tokens')}, cached {usage.get('cached_input_tokens')})", True, hard=False)
        subprocess.run([sys.executable, str(Path(__file__).resolve()), "done", meta["run_id"], "--force"],
                       capture_output=True, text=True)
    else:
        check("a run was recorded", False, detail="no 'RUN <id>' line in the output")

    print("SELFTEST")
    for name, ok, hard, detail in checks:
        tag = "ok  " if ok else ("FAIL" if hard else "warn")
        print(f"  {tag} {name}" + (f"  [{detail}]" if detail and not ok else ""))
    passed = all(ok for _, ok, hard, _ in checks if hard)
    try:
        ver = subprocess.run([codex_bin() or "codex", "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        ver = "unknown"
    write_selftest_record(SELFTEST_FILE, {"codex_version": ver, "model": a.model, "ts": time.time(),
                                          "result": "PASS" if passed else "FAIL", "tool_version": VERSION,
                                          "run": meta.get("run_id") if meta else None})
    print("SELFTEST " + ("PASS" if passed else "FAIL") + f"   (scratch repo kept at {d})")
    return EXIT_PASS if passed else EXIT_FAIL


def build_parser():
    p = argparse.ArgumentParser(prog="codex-wp", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"codex-wp {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="is the Codex seat usable right now? (login, quota pace, slots)")
    c.add_argument("--probe", action="store_true", help="make one tiny real call (~15k tokens) to refresh the quota snapshot")
    c.add_argument("--model", default=DEFAULT_MODEL)
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("run", help="dispatch one WP to a Codex worker in its own worktree, then check the result")
    r.add_argument("wp", help="path to the WP markdown file (needs a 'Files owned:' line)")
    r.add_argument("--repo", default=".")
    r.add_argument("--base", default="HEAD", help="commit/branch the worker is cut from (a revision = a new WP on the previous wp/ branch)")
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--effort", help="model_reasoning_effort override (e.g. low, medium, high)")
    r.add_argument("--tdd", action="store_true", help="require that the WP's verify command FAILS on the base commit first")
    r.add_argument("--setup", help="shell command run in the worktree before the worker starts (e.g. dependency install; the worker has no network)")
    r.add_argument("--verify-now", action="store_true", help="run the WP's verify commands right after the worker (they execute worker-written code outside the sandbox: only for trusted repos, otherwise read the diff first and use `codex-wp verify`)")
    r.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    r.add_argument("--force-pace", metavar="REASON", help="send this WP although the quota is ahead of pace (needs a reason, it is logged)")
    r.set_defaults(func=cmd_run)

    v = sub.add_parser("verify", help="run a finished run's 'Verify with:' commands in its worktree (after you read the diff)")
    v.add_argument("run")
    v.add_argument("--verbose", action="store_true")
    v.set_defaults(func=cmd_verify)

    rv = sub.add_parser("review", help="recompute the mechanical review of a run (after you or the worker edited its worktree)")
    rv.add_argument("run")
    rv.set_defaults(func=cmd_review)

    s = sub.add_parser("status", help="seat summary and the latest runs")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.set_defaults(func=cmd_status)

    d = sub.add_parser("done", help="remove a run's worktree (the branch is always kept)")
    d.add_argument("run")
    d.add_argument("--force", action="store_true")
    d.set_defaults(func=cmd_done)

    fo = sub.add_parser("follow", help="watch a run live (commands, edits, agent messages); read-only, made for a tmux pane")
    fo.add_argument("run", nargs="?", help="run id or unique prefix; default: the newest run")
    fo.add_argument("--no-wait", action="store_true", help="replay what exists and exit")
    fo.set_defaults(func=cmd_follow)

    t = sub.add_parser("selftest", help="end-to-end positive control with a real Codex call (~150k tokens)")
    t.add_argument("--model", default=DEFAULT_MODEL)
    t.set_defaults(func=cmd_selftest)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except GitError as e:
        print(f"GIT ERROR: {e}", file=sys.stderr)
        return EXIT_USAGE
    except WPError as e:
        print(f"USAGE: {e}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
