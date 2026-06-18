---
title: "Codex team lifecycle — Nat's proven recipe vs our naive setup"
date: 2026-06-16
source: "gist/nazt/319bce17 + gap analysis against pops-clinic pilot"
confidence: high
tags: [codex, maw, team, lifecycle, omx, charter, branch-isolation]
---

## Pattern: /codex-team skill

Nat's proven recipe for managing Codex builder teams. Key differences from our initial pops-clinic setup:

### What we got wrong (fixable)

1. **Engine name**: `omx` not `codex` — affects maw team routing
2. **Charter location**: should be `ψ/teams/` (brain-committed), not `.maw/teams/`
3. **No branch isolation**: each member needs own branch + worktree
4. **Dispatch**: `maw hey` not `tmux send-keys` (send-keys is Trap #1!)
5. **No lifecycle**: we only had "spawn" — need up/down/status/restart/scale

### What we got right

1. AGENTS.md + agents/*.md for project context (Codex reads automatically)
2. PM Oracle as lead (reviews + commits)
3. Role-based naming (chrome/flux/static)
4. Decision tree: when Codex vs when Claude subagent

### Lifecycle commands

```
maw team preflight ψ/teams/[team].yaml   # check before spawn
maw team up [name]                       # spawn (skip-live)
maw team up [name] --only codex-N        # relaunch single member
maw hey codex-N "task"                   # dispatch work
maw peek [session]:codex-N              # monitor
maw team down [name]                    # teardown (auto-save WIP)
```

### Key rules from Nat

- Charter is source of truth (ψ/teams/)
- `maw hey` only for omx (SendMessage = silent no-op)
- Confirm dead with `maw peek` before relaunch
- PRs to alpha, never main
- Oracle reviews, human approves
