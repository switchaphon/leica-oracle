# /codex-team Skill — Architecture Analysis

> Source: https://gist.github.com/nazt/319bce17aa49ca6e9ac9529414e903ee
> Analyzed: 2026-06-16 by Leica

## What It Is

A Claude Code skill (`/codex-team`) that manages the full lifecycle of a Codex builder team. Proven recipe from Nat's arra-oracle-v3 project (ting/tee pattern).

## Architecture: Claude Lead + OMX Codex Builders

```
Oracle (Claude CLI) — the lead
  │
  ├── maw team up [name]       → spawn team
  ├── maw team down [name]     → teardown
  ├── maw peek [session:name]  → monitor
  ├── maw hey [name] "task"    → dispatch work
  │
  └── codex-1..7 (OMX engine)  → builders
       ├── each gets own branch (agents/arra-codex-N)
       ├── each gets own worktree
       ├── each creates PR to alpha branch
       └── Oracle reviews + Nat approves merge
```

## Key Components

### 1. Charter YAML (in ψ/teams/, NOT .maw/teams/)
```yaml
name: arra-oracle-v3-team
members:
  - role: lead
    name: arra-oracle-v3
    engine: claude
    worktree: false           # lead stays in main tree
  - role: codex-1
    name: codex-1
    engine: omx               # NOT "codex" — uses omx
    branch: agents/arra-codex-1
    prompt: |
      ...task contract...
```

### 2. Lifecycle Actions
| Action | Command | What it does |
|--------|---------|-------------|
| up | `maw team up [name]` | Preflight → spawn tmux windows + worktrees |
| down | `maw team down [name]` | Auto-save WIP → kill windows → remove worktrees |
| status | `maw peek [session:name]` loop | Peek each pane + check PRs |
| restart | down + sleep 3 + up | Fresh start |
| scale N | Edit YAML + `--only codex-N` | Add members without touching existing |

### 3. Branch Isolation
Each codex member:
- Has own git branch: `agents/arra-codex-N`
- Has own worktree (via maw team)
- Creates PR to `alpha` branch (never main)
- Oracle reviews, human approves merge

### 4. Key Rules
1. Charter is source of truth: `ψ/teams/*.yaml`
2. NAME vs PATH: up/down use NAME, preflight uses PATH
3. Dispatch via `maw hey` only (not SendMessage — silent no-op on omx)
4. Confirm with `maw peek` before assuming dead
5. Targeted relaunch: `--only codex-N`
6. Never push to main
7. Never auto-merge PRs

## Scale: 7 Codex Members
The arra-oracle-v3 runs 7 parallel codex builders — far beyond our pops-clinic 3-member setup. Each on isolated branch + worktree.
