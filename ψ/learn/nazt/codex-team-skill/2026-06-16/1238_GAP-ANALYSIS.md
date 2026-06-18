# Gap Analysis: Our Codex Setup vs Nat's Proven Recipe

> Compared: pops-clinic codex-squad (Leica's setup, 2026-06-15) vs /codex-team skill (Nat's gist)

## Side-by-Side

| Aspect | Our Setup (pops-clinic) | Nat's Proven Recipe |
|--------|------------------------|---------------------|
| **Charter location** | `.maw/teams/codex-squad.yaml` | `ψ/teams/*.yaml` (brain-committed) |
| **Engine** | `codex` | `omx` |
| **Members** | 3 (chrome, flux, static) | 7 (codex-1..7) |
| **Branch isolation** | None — all on same branch | Each member own branch + worktree |
| **Lifecycle** | Manual spawn only | up/down/status/restart/scale |
| **Preflight** | None | `maw team preflight` before spawn |
| **Status monitoring** | Ad-hoc `tmux capture-pane` | `maw peek` loop |
| **Dispatch** | `tmux send-keys` | `maw hey` (proper routing) |
| **Task assignment** | Inline prompt in codex exec | `maw hey [name] "task"` |
| **PR workflow** | None — PM Oracle commits directly | Each member → PR to alpha → review |
| **Teardown** | Manual `tmux kill-pane` | `maw team down` (auto-save WIP) |
| **Dead member recovery** | None | `--only codex-N` targeted relaunch |
| **Scale** | Edit YAML manually | Scale command with template |

## Critical Gaps (ordered by impact)

### 1. No Branch Isolation (HIGH)
Our setup has all 3 codex members working on the same branch. If they edit the same file → conflict. Nat's recipe gives each member its own branch + worktree.

### 2. No Lifecycle Management (HIGH)
We only documented "how to spawn" — no teardown, no status check, no restart, no scale. PM Oracle has to manage tmux manually.

### 3. Engine Name: codex vs omx (MEDIUM)
Nat uses `omx` not `codex`. Need to verify which is current — may affect maw routing.

### 4. Charter Location (MEDIUM)
We put charters in `.maw/teams/` (project dir, gitignored). Nat puts in `ψ/teams/` (brain, committed). Brain-committed means charter survives across sessions and is part of Oracle identity.

### 5. No Preflight Check (LOW)
`maw team preflight` catches issues before spawn (worktree conflicts, missing branches). We skip it.

### 6. Dispatch Method (LOW)
We use `tmux send-keys` (known buggy — Trap #1 in playbook). Nat uses `maw hey` which routes properly.

## What To Update

1. **Charter**: Move to `ψ/teams/` and add branch isolation per member
2. **Engine**: Verify `omx` vs `codex` naming with Un
3. **Lifecycle**: Install or create `/codex-team` skill for PM Oracles
4. **CLAUDE.md Step 4**: Update commands to use maw hey + lifecycle
5. **docs/codex-agents.html**: Add lifecycle section, fix architecture diagram
6. **Playbook**: Add lifecycle commands to the Codex Team Playbook
