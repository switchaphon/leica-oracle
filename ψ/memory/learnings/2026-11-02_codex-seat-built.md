# Codex seat: verified, four beliefs overturned, wrapper built (2026-11-02)

Un re-subscribed to ChatGPT and asked for the fleet to run as "Opus leads, Codex works".
Everything below was run on this machine on 2026-11-02, not read from config.

## What is true now

- `codex exec` works headless from the Bash tool (codex-cli 0.144.1, default model gpt-5.6-sol).
- The subscription has ONE weekly window and no credits. The quota is readable from a rollout:
  `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, event `token_count`, field `rate_limits`
  (`primary.used_percent`, `window_minutes`, `resets_at`). It only moves when Codex runs.
- Un confirmed the tier. After about 0.3M tokens of tests the meter still read 0.0%, so the real capacity is unmeasured.
- `omx exec` also works, but `omx doctor` shows its setup is gone from `~/.codex` (no prompts, 1 of 27 skills,
  no AGENTS.md, no OMX entries in config.toml): the ChatGPT desktop app rewrote that directory on 27 Oct.
  Without the setup, `omx exec` is plain `codex exec`. Installed 0.18.13, npm latest 0.21.46; its default
  lanes still name gpt-5.5, which this account's model list does not offer.

## Four beliefs that did not survive the run

1. "`workspace-write` cannot `git commit`" (Trap 11). In a linked worktree the worker committed. Do not rely on the sandbox to stop commits.
2. "The 17k-token overhead of a trivial prompt comes from the desktop app's plugins and MCP." Measured: 17,134 with the config, 16,565 with `--ignore-user-config`. It is Codex's own base instructions and tool schemas. Per WP the input is about 130k tokens (92% cached) for a three-line task.
3. "The models-cache parse error was transient." It returns whenever the desktop app (0.164.0-alpha) has rewritten `models_cache.json` since the last CLI (0.144.1) run. Harmless fallback; never treat it as a failure.
4. "`dispatch_external.sh --check` proves the seat is reachable." It ran `codex --version`: a binary, not a login. The same script defaulted to gpt-5.5, which is not in the account's model list.

My own first review of the test run also looked at `git diff` (empty) while the worker had already committed two junk files.
The review has to diff `base..HEAD`.

## What was built

`ψ/lab/codex-wp/` (stdlib Python, installed to `~/.claude/bin/codex-wp`): seat check, weekly pace, slots, worktree per WP,
sandboxed `codex exec`, success only on `turn.completed`, ownership and junk checks against `base..HEAD`, `--tdd`, `selftest`.
62 unit tests; 12 deliberate bugs were injected and all 12 were caught. `selftest` passed end to end.
The agent-team skill's `scripts/dispatch_external.sh` is now a shim for it (original kept as `.orig-2026-11-02`).

## What /learn of maw-codex-team-kit added (docs in ψ/learn/Soul-Brews-Studio/maw-codex-team-kit/)

- The kit's verbs are gone from maw-rs for a structural reason: a native `codex` command shadows a plugin of that name.
  Relinking the plugin would not help. Nothing in the kit is worth reviving; its bugs are the failure classes `codex-wp` tests for.
- Applied at once: the kit's charter parser kept `# comments` inside values, so a note glued to a `Files owned` path
  in a WP would have silently failed every ownership check. `parse_wp` now refuses it (2 tests, red first).
- maw-rs' own convention is YOLO workers, because sandboxed TUI workers stall on approvals. `codex exec` never asks, so it
  avoids that, at the price of no network and no writes outside the worktree. The pilot has to show whether that is enough.
- Installed maw-rs (alpha.1027) is six weeks behind the newest release (alpha.2316, 2026-09-12). Not touched.

## Still open

- Pilot in pops-vet-oracle (Un approved the pilot and lifting the 2026-07-29 "Opus writes the code" rule for that oracle). Not started.
- DNA letter to the 15 sons, after the pilot gives real numbers. Three sons hold contradictory Codex memories (dead, suspended, codex-first); twelve hold none.
- `/dig --codex`: dig.py reads only `~/.claude/projects`.
- omx as an optional second layer: needs `omx setup` into `~/.codex` (the desktop app's directory), an upgrade, and a decision about a separate CODEX_HOME.
