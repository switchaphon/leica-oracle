# codex-wp

Hand one work package (WP) to a Codex worker, then check mechanically what came back.
Built 2026-11-02 (v0.1.1) for the "Opus leads, Codex works" setup. Stdlib Python 3, no dependencies.

## The contract

| Who | Does |
|---|---|
| Lead (an Opus oracle) | designs with Un, writes the WP, **reads the diff**, decides, merges |
| `codex-wp` | checks the seat, cuts a worktree, runs the worker, proves what a script can prove |
| Codex worker | implements exactly the WP, inside its own worktree, sandboxed |

`codex-wp` never judges the work. A PASS means "nothing mechanical is wrong", not "this is good".

## 0.1.6

Before setup, the secret preflight scans the base checkout's tracked files and the WP text.
It runs gitleaks from each scan directory so the worktree's `.gitleaks.toml` and
`.gitleaksignore` apply there, and checks URLs for embedded credentials. Like gitleaks findings,
`url-credential` findings honour `gitleaks:allow` on the source line (including in WP text)
and `.gitleaksignore` fingerprints `<file>:url-credential:<line>` for worktree files.
The URL check skips
tracked files larger than 1,000,000 bytes and files with a NUL byte in the first 8192 bytes.
Loopback, placeholder and default URL credentials are noted, not blocked. Findings show
only their source, rule, file and line, never credential values. Missing or broken gitleaks
fails closed with PRECONDITION before setup or the worker starts. Install it with
`brew install gitleaks`, or set `CODEX_WP_GITLEAKS` to an executable.
`--no-secret-scan REASON` is for a human: auto mode refuses it in an AI session.
An AI session's way forward is a reviewed marker committed by the repo owner, or a
FALLBACK subagent. A human's skip reason is printed and recorded in `meta.json`.
A blocked run prints `codex-wp done <run-id>` for cleanup.

The scan result is cached per base tree (the tree, not the commit) in
`~/.codex-wp/cache/preflight/`. The key includes the tree, the gitleaks binary's resolved
path, size and modification time, codex-wp's version, and `GITLEAKS_CONFIG` /
`GITLEAKS_CONFIG_TOML` (including the config file's contents). Only worktree findings
are cached; the WP text is always scanned fresh. Failed or timed-out scans are never
cached. Entries older than 14 days are removed when a new entry is written.
`--rescan` ignores the cache and scans the tree again.

`--scan-timeout SECONDS` (default 900) bounds each gitleaks call; a timeout fails closed.
Gitleaks took 216 s on a 778 MB repo. A timed-out run suggests doubling the scan timeout:
a finished scan is cached, so only the first run on a tree waits. The scan still runs
while the run holds a Codex slot. Repeated noted lines are shown once, capped at 5,
with the rest in `meta.json`; the record keeps every hit, including repeats.
Blocking lines are shown once each and are never capped. `meta.json` also records
`scan_timeout_s` and whether the scan used the cache, its base tree and scan duration.

The sandbox limits writes, not reads: a worker can read files outside the worktree.
In November 2026 workers read `~/.agents/skills` on their own. The preflight stops a
dispatch into secrets but does not confine what a worker can read. It scans before setup,
so it does not cover files created by setup or later worker reads.

`run --wait SECONDS` waits for a free slot for up to that many seconds, printing WAIT
messages. The default is 0, which returns BUSY immediately; negative values are rejected.
After waiting, the tool checks the seat again and releases the slot if dispatch is no
longer allowed. `--force-pace REASON` can override HOLD only, including after a wait.

A PASS without tool-run verification now says:

```text
RESULT  PASS  (mechanical checks only; verify not run by the tool: read the report, then codex-wp verify)
  report   <first non-empty line outside fenced blocks in the worker report>
```

The report head is the worker's own text, with heading marks and terminal controls removed
and long lines clipped. It is not an independent verdict. `--verify-now` runs the WP's
verify commands; a PASS after green verification prints exactly `RESULT  PASS`.
`meta.json` records `report_head`, `timeout_s` and `verify_state`: `no commands`, `not run`,
`green` or `red`. A later `codex-wp verify` updates `verify_state` to `green` or `red`.

## Quick start

```bash
CW=~/.claude/bin/codex-wp
$CW check                         # login, weekly pace, free slots (no model call)
$CW run wp-1.md --repo . --tdd    # dispatch; use Bash run_in_background for WPs longer than a few minutes
$CW follow                        # in a tmux pane: watch the newest run live (commands, edits, agent messages); read-only
git -C <worktree> diff <base>..HEAD   # READ THE DIFF (run prints the exact command)
$CW verify <run-id>               # after you read it: run the WP's "Verify with:" commands
$CW done <run-id>                 # remove the worktree; the branch is always kept
```

## WP format

```markdown
## WP-1: short title
- Goal: what done looks like
- Files owned: add.py, src/lib/**          (required; comma separated, globs allowed, no overlap with other WPs)
- Ignore: dist-test/                        (optional: generated paths the repo's own test script leaves behind; never committed, not a violation)
- Context: interfaces and conventions the worker needs, nothing else
- Constraints: style, allowed dependencies
- Acceptance criteria: checkable list
- Verify with: python3 -m unittest -q test_add     (one line per command, or an indented bullet list)
- Report back: files changed, key decisions, verify output, unresolved items
```

A WP without `Files owned:` is refused. Ambiguity belongs to the lead; never send it to a worker.

## What `run` does, in order

1. `check`: login valid, quota on pace, a free slot (3 fleet-wide). Otherwise it stops with an exit code and says what to do.
2. `--tdd` (use it for new behaviour): the `Verify with:` command must **fail** on the base commit. A test that cannot fail proves nothing.
   It runs in a worktree that got the same `--setup` as the worker (without it a verify that needs `node_modules` fails for the
   wrong reason and the red is fake; found by pops-658 on the first pilot run), and the output ends with the first failure line:
   read it and check it is the right red.
3. Cuts `wp/<run-id>` in a worktree under `~/.codex-wp/worktrees/`, from `--base` (default `HEAD`).
4. Runs the secret preflight before setup, then `codex exec -s workspace-write --json --ignore-user-config -c shell_environment_policy.inherit=core`, prompt on stdin.
   Never a bypass flag (the code refuses `danger-full-access`). The worker has no network.
5. Success needs `turn.completed` in the event log **and** a non-empty report. Exit code 0 alone is not proof.
6. The wrapper, not the worker, stages and commits only dirty paths that are in `Files owned` and are not junk.
7. Review is against `base..HEAD`, never the working tree: a worker that commits leaves `git diff` empty.
   Changed paths outside `Files owned`, or junk that got committed, make the result REVISE.

Run records live in `~/.codex-wp/runs/<run-id>/` (`wp.md`, `prompt.md`, `events.jsonl`, `report.md`, `stderr.txt`, `meta.json`).

## Exit codes

| Code | Meaning | The lead should |
|---|---|---|
| 0 | PASS / GO | read the diff, then `verify` |
| 2 | usage (bad WP, not a git repo) | fix the input |
| 10 | HOLD: ahead of the weekly pace | wait, or `--force-pace "reason"` for urgent work |
| 11 | BUSY: no free slot | wait |
| 12 | UNAVAILABLE: not logged in, no binary, quota at the hard stop | fall back to a Claude subagent labelled FALLBACK, or wait for the reset |
| 14 | PRECONDITION: TDD check refused, secrets found, or secret scan failed | fix the test or resolve the secret preflight |
| 20 | REVISE: violations, junk, nothing owned changed, or verify failed | send a new WP on top of the branch |
| 30 | FAIL: worker error, timeout, no `turn.completed`, empty report | look at `events.jsonl` and `stderr.txt` |

## Pacing

The subscription has a weekly window and no credits. The quota is read from the newest rollout's
`token_count.rate_limits` (so it only moves when Codex runs; `check --probe` spends ~15k tokens to refresh).

- allowed = min(85, elapsed% + 10) for windows of a day or longer; shorter windows only use the 85 cap
- used > allowed: HOLD. used >= 90 or a limit reached: UNAVAILABLE
- the cap is shared with Un's own Codex use, so the fleet must not spend the week in a day

## Revisions

A revision is a new WP based on the previous branch: `codex-wp run wp-1b.md --base wp/<previous-run-id>`.
Keep the feedback precise; after two rounds the spec is the problem, not the worker.

## Watching a run, and cleaning up

`codex-wp follow [run-id]` is a read-only live view made for a tmux pane: the commands the worker runs with their exit codes, its
edits, what it says, and the final token line. It replays what exists, follows new events, and ends by itself when the run reaches
a final status (`--no-wait` replays and exits). It does not change how the lead dispatches: the lead still runs `codex-wp run` in
the background, and a person opens `follow` wherever they want to watch. When `codex-wp run` is itself started in a tmux pane, its
stdout is a terminal and the same live view prints in that pane by default (`--no-follow` turns it off; `--follow` forces it).

`codex-wp done <run-id>` removes the worktree and keeps the branch. It used to refuse a worktree whose only untracked content was
a symlink made by `--setup` (typically `node_modules`). Now symlinks and generated junk do not block it (a link's target is never
touched); any real untracked file still does.

## Install and test

```bash
./install.sh                       # runs the unit tests, copies to ~/.claude/bin/codex-wp, backs up any old copy
python3 -m unittest -q test_codex_wp   # offline, no Codex call
codex-wp selftest                  # one real Codex call; a claim that "Codex is dead" needs this to FAIL first
```

The unit tests were mutation-checked on 2026-11-02: 12 deliberate bugs, all caught.

### Version drift

A passing selftest proves only the Codex version and model it ran on. `selftest` writes them to `~/.codex-wp/selftest.json`.
`check` and `run` print a `selftest WARN` line when the Codex CLI or the pinned model is not the one that passed, when the last
selftest failed, or when the pass is older than three days. It is a warning, not a block. Why it exists: on 2026-11-02 at 16:36
someone upgraded the CLI from 0.144.1 to 0.166.0, fifty minutes after the only selftest and minutes before the first pilot
window could dispatch. Nothing told the lead. After any Codex upgrade, run `codex-wp selftest` before the next WP.

## Not done yet (v0.1)

- `verify` runs worker-written code outside the sandbox. Read the diff first. `--verify-now` is for trusted repos only.
- No `omx` or `maw team` engine. `codex exec` directly is the default; see the learnings note for why.
- `/dig` does not read Codex rollouts (`~/.codex/sessions`) yet.
- Codex has a built-in command policy. It screens the commands the worker types, not what a script it runs does: `rm -rf` typed by
  the worker is rejected (and the whole compound command with it), while the repo's own `pnpm test`, which starts with `rm -rf dist-test`,
  runs fine. Found on pops-655: the worker could not delete the folder its tests create, so it moved it to /tmp to satisfy the old rule
  "leave nothing behind". Since 0.1.3 the preamble says: delete what you can; if the sandbox refuses, leave it, name it in the report,
  never move or hide it. The lead declares such paths with `Ignore:` in the WP (and should add them to the repo's `.gitignore`).
- Workers on Codex CLI 0.166.0 read skills from `~/.agents/skills` (45 on this machine) on their own initiative, for example
  `test-driven-development`. `--ignore-user-config` does not stop that and `codex features list` has no switch for it. The
  WP and the repo's AGENTS.md should carry what matters; `events.jsonl` (or `follow`) shows when a skill was read. Open question:
  forbid it in the preamble? Changing the preamble changes worker behaviour, so not done mid-pilot.
- Local commits made by this tool are intermediate. The lead squashes or amends and adds the Rule 8 signature before any push.
