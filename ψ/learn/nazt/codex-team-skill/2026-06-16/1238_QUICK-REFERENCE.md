# /codex-team Quick Reference

> From Nat's gist — proven recipe for arra-oracle-v3

## Commands

```bash
# Spawn
maw team preflight ψ/teams/[team].yaml   # preflight check
maw team up [team-name]                   # spawn all members

# Monitor
maw peek [session]:[member]               # peek at one member
for N in 1 2 3; do maw peek [session]:codex-$N 2>&1 | tail -10; done

# Dispatch
maw hey codex-1 "task description"        # send task to member

# Teardown
maw team down [team-name]                 # auto-save + kill + cleanup

# Restart
maw team down [name] && sleep 3 && maw team up [name]

# Targeted relaunch (one dead member)
maw team up [team-name] --only codex-N

# Scale (add members)
# Edit ψ/teams/[team].yaml → add new member entries
maw team up [team-name] --only codex-NEW
```

## Charter Template

```yaml
# ψ/teams/[project]-team.yaml
name: [project]-team
description: Claude lead + Codex builders

members:
  - role: lead
    name: [oracle-name]
    engine: claude
    worktree: false

  - role: codex-1
    name: codex-1
    engine: omx
    branch: agents/[project]-codex-1
    prompt: |
      You are codex-1, a builder for [project].
      Work ONLY on your branch agents/[project]-codex-1.
      Read AGENTS.md + agents/[role].md for context.
      When done: create PR to alpha, print DONE with file summary.

  - role: codex-2
    name: codex-2
    engine: omx
    branch: agents/[project]-codex-2
    prompt: |
      ...same pattern...
```

## Status Table Format

```
| Member   | State        | Current Task          | PR    |
|----------|--------------|-----------------------|-------|
| codex-1  | working (5m) | Build AppointmentPicker | #42  |
| codex-2  | standby      | —                     | —     |
| codex-3  | done         | Refactor utils        | #43   |
| codex-4  | dead         | — (relaunch needed)   | —     |
```

States: `working (Nm)` / `standby` / `done` / `blocked` / `dead`

## Key Rules

1. Charter in `ψ/teams/` (not `.maw/teams/`)
2. `maw hey` for dispatch (not tmux send-keys, not SendMessage)
3. Confirm dead with `maw peek` before relaunching
4. Each member gets own branch + worktree
5. PRs to alpha, never main
6. Oracle reviews, human approves merges
