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
4. Runs `codex exec -s workspace-write --json --ignore-user-config -c shell_environment_policy.inherit=core`, prompt on stdin.
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
| 14 | PRECONDITION: `--tdd` and verify already passes on base | fix the test |
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
the background, and a person opens `follow` wherever they want to watch.

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
- Workers on Codex CLI 0.166.0 read skills from `~/.agents/skills` (45 on this machine) on their own initiative, for example
  `test-driven-development`. `--ignore-user-config` does not stop that and `codex features list` has no switch for it. The
  WP and the repo's AGENTS.md should carry what matters; `events.jsonl` (or `follow`) shows when a skill was read. Open question:
  forbid it in the preamble? Changing the preamble changes worker behaviour, so not done mid-pilot.
- Local commits made by this tool are intermediate. The lead squashes or amends and adds the Rule 8 signature before any push.
