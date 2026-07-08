---
name: maw-new-wake-work
description: maw new vs wake vs work — 3 tmux workspace commands, different intent and defaults
metadata:
  type: reference
---

## maw new vs wake vs work

Three commands for tmux workspaces, overlapping surface but different intent:

| Command | Purpose | Oracle resolve | Worktree | Default engine |
|---------|---------|---------------|----------|----------------|
| `maw new` | Raw tmux session/split | No | No | None (bare shell) |
| `maw wake` | Wake oracle by name | Yes (ghq+fleet+fuzzy) | Naming only (--wt slug) | `codex` |
| `maw work` | Repo + optional worktree | Yes (ghq+path+URL) | Full (--wt creates agents/<slug>) | `claude` |

**Key differences:**
- `maw wake` has deterministic hash slot (10-89) for collision avoidance
- `maw work --wt` creates actual git worktrees for isolation
- `maw new --claude` auto-wires `CLAUDECODE=1` + `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- Only `maw wake` supports `--peer` for remote fleet

**Codex team spawn recipe:**
```bash
for i in 1 2 3 4 5; do
  maw work . coder-$i --wt --fresh -e codex
done
```

**Teardown:**
```bash
for i in 1 2 3 4 5; do
  tmux kill-window -t "coder-$i" 2>/dev/null
  git worktree remove agents/coder-$i --force 2>/dev/null
done
```

Source: Nat's maw-command-ref.html (2026-07-06), from maw-rs crate `workspace_scaffold_commands.rs`
