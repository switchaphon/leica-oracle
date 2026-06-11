# Codex CLI — Traps, Patterns & Integration Guide

> Learned: 2026-06-10  
> Context: Un tried to `maw swarm codex` for POPS prototype work and hit 3 errors in a row.  
> Source: Hands-on debugging + Soul-Brews-Studio/maw-js docs (Marathon Day 4)

---

## The 3 Traps Un Hit

### Trap 1: `--full-auto` doesn't exist

Codex CLI is NOT Claude Code. Flag names are completely different.

| Claude Code | Codex CLI equivalent |
|---|---|
| `claude --dangerously-skip-permissions` | `codex exec -s danger-full-access` |
| `claude -p "prompt"` | `codex exec "prompt"` |
| `claude` (interactive) | `codex` (interactive TUI) |
| N/A | `codex exec -s workspace-write "prompt"` (non-interactive, scoped write) |

### Trap 2: ChatGPT auth ≠ API auth

`codex doctor` shows `stored auth mode: chatgpt` — this BLOCKS most models.

The error `o4-mini not supported with ChatGPT account` fires even when `-m` is NOT passed, because gpt-5.5 (default) internally delegates to o4-mini.

**Fix**: `codex login --api-key` → provide OpenAI API key (costs per token).  
**Check**: `codex doctor 2>&1 | grep -A 5 "auth"`

### Trap 3: `maw swarm` ≠ `maw team`

`maw swarm codex` runs bare `codex` (interactive TUI). No prompt injection, no coordination, no worktree isolation.

**`maw swarm`** = quick A/B panes. No coordination layer.  
**`maw team`** = charter-driven, worktree-isolated, reincarnation-capable. This is what Nat uses.

---

## The Nat Pattern: `maw team` + Charter YAML

From Marathon Day 4 (Soul-Brews-Studio, 2026-06-07): Nat ran 4 Codex agents simultaneously on maw-js using team charters.

### Charter YAML structure

```yaml
# .maw/teams/<team-name>.yaml
name: my-team
description: Coordinated claude + codex squad
members:
  - role: oracle
    engine: claude
    repo: path/to/repo
    prompt: "You are the lead oracle..."
  
  - role: builder-1
    engine: codex
    repo: path/to/repo
    prompt: "You are builder-1. Task: ..."

  - role: builder-2
    engine: codex
    repo: path/to/repo
    prompt: "You are builder-2. Task: ..."
```

### Lifecycle commands

```bash
# Spawn team (OMX_AUTO_UPDATE=0 prevents codex self-update)
OMX_AUTO_UPDATE=0 maw team up my-team

# Monitor
maw peek SESSION:member-name --lines 15

# Send instructions
maw hey SESSION:member-name "new task or context"

# Graceful shutdown
maw done member-name

# Cleanup orphan worktrees
git worktree prune && mv agents/1-codex-* /tmp/
```

### `maw swarm` vs `maw team`

| | `maw swarm` | `maw team` |
|---|---|---|
| Config | none (bare command) | charter YAML |
| Prompt | manual type/paste | from charter |
| Worktree | shared cwd | isolated per member |
| Crash recovery | none | `maw team resume` |
| Coordination | none | charter + heartbeat |
| Use case | quick A/B test | real work |

---

## maw.config.json — Codex Engine Config

### `commands` field (pattern matching for `maw wake`)

```json
"commands": {
  "default": "claude --dangerously-skip-permissions --continue",
  "*-oracle": "claude --dangerously-skip-permissions --continue",
  "codex-*": "codex --dangerously-bypass-approvals-and-sandbox"
}
```

Note: Nat's docs used `--dangerously-auto-approve` — that flag no longer exists in Codex v0.139.0+.  
Current equivalent: `--dangerously-bypass-approvals-and-sandbox`

### `engines` field (newer, used by `maw swarm`)

```json
"engines": {
  "codex": {
    "cmd": "codex",
    "label": "Codex CLI"
  }
}
```

The default engine registry already has this — only override if you need custom flags.

---

## Known Traps (from Nat's Marathon Day 4)

| Trap | Fix |
|---|---|
| `codex idle (0 in / 0 out)` after spawn | Prompt arrives before agent ready — known bug #2416 |
| `OMX_AUTO_UPDATE=0` not set | Codex updates itself mid-task, breaks everything |
| Orphan worktree blocks `team up` | `git worktree prune && mv agents/* /tmp/` before re-spawn |
| `maw peek` after gather shows wrong pane | Use `oracle.N` index, not `codex-N` name |
| Charter issues all closed | Check `gh issue view N --json state` before spawn, update YAML |

---

## Codex exec Quick Reference

```
codex exec [OPTIONS] [PROMPT]

-m, --model <MODEL>          o3, o4-mini, gpt-5.5, etc.
-s, --sandbox <MODE>         read-only | workspace-write | danger-full-access
-p, --profile <NAME>         Load ~/.codex/<name>.config.toml
-i, --image <FILE>           Attach image(s)
--output-schema <FILE>       JSON Schema for structured output
```

| Sandbox | Read | Write | Risk |
|---|---|---|---|
| `read-only` | workdir | nothing | safe |
| `workspace-write` | workdir, /tmp | workdir, /tmp | medium |
| `danger-full-access` | everything | everything | high |

---

## Auth: RESOLVED (2026-06-11)

~~Without `codex login --api-key`, Codex cannot execute ANY task.~~

**Fixed**: ChatGPT Pro (20x plan) works with Codex CLI as-is. The o4-mini error was a temporary OpenAI server-side bug, not an auth limitation. No API key needed.

```bash
codex doctor 2>&1 | grep "auth mode"   # → chatgpt (this is fine)
codex exec -s workspace-write "echo hello"  # → works on Pro plan
```

**Note**: Must run inside a git repo (or use `--skip-git-repo-check`).

## Charter Issues Found During Live Test (2026-06-11)

### Lead prompt delivered as raw text
The charter `prompt:` field gets sent via `maw hey` after the agent pane opens. For Codex, this works because Codex has an input prompt. For Claude lead, the prompt was sent to a zsh shell and interpreted as a command → `zsh: no matches found: [leica:leica]`.

**Fix**: Lead should either:
- Have `engine: claude` and be spawned properly (maw wake starts claude CLI)
- Or use `prompt: |` with a file path reference instead of inline text

### codex-2 garbled input
Existing text in the pane buffer ("ปิดcode") corrupted the agent start. The `--gather` then couldn't join the dead pane.

**Fix**: Always `git worktree prune` before `maw team up` to start clean.
