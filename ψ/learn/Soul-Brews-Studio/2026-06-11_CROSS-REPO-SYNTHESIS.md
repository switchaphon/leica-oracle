# Cross-Repo Synthesis: Claude Code + Codex Integration

> Deep explored 2026-06-11 | 15 agents × 3 repos | Focus: how Claude Code works with Codex

## The 3 Repos & How They Relate

```
arra-oracle-skills-cli          multi-agent-workflow-kit          maw-js
(skill distribution)            (worktree isolation)              (orchestration engine)
        │                               │                              │
        │ installs skills to            │ provides git worktree       │ resolves engines,
        │ 19 agents including           │ isolation + tmux layouts    │ spawns teams,
        │ Claude + Codex                │ for parallel agents         │ routes messages
        │                               │                              │
        └───────────┬───────────────────┴──────────────────────────────┘
                    │
         All three serve the same goal:
         Run multiple AI agents (Claude, Codex, OpenCode, Aider)
         working on the same codebase without conflicts
```

## Answer: Yes, They're Related

| Repo | Role | Codex Integration |
|------|------|-------------------|
| **arra-oracle-skills-cli** | Installs skills to `~/.codex/skills/` + plugin marketplace | Codex 0.128+ TOML, 0.130+ JSON format |
| **multi-agent-workflow-kit** | Git worktree isolation for parallel agents | agents.yaml `model:` field (metadata only) |
| **maw-js** | Engine registry + team charter orchestration | First-class engine with capability limits |

## Key Finding: 3 Layers of Codex Support

### Layer 1: Skill Installation (arra-oracle-skills-cli)
- Installs Oracle skills to `~/.codex/skills/` and `~/.codex/prompts/`
- Codex plugin marketplace integration (TOML for v0.128, JSON for v0.130+)
- `npx arra-oracle-skills install -g -y --agent codex`

### Layer 2: Worktree Isolation (multi-agent-workflow-kit)
- Each agent gets isolated `agents/<name>/` directory + branch
- Engine-agnostic: doesn't care what runs in each tmux pane
- `.codex/prompts/` auto-synced from `.claude/commands/`
- `maw hey <agent> "task"` works regardless of engine

### Layer 3: Engine Orchestration (maw-js)
- **Engine Registry**: `config.engines.codex = { cmd: "codex", label: "Codex CLI" }`
- **Team Charter**: `engine: codex` per member with charter-local engine overrides
- **Capability Gates**: Codex lacks resume, channels, model, system-prompt-file
- **Fail-Loud Validation** (#2707): Unresolvable engines abort before spawn

## Codex vs Claude: Capability Comparison in maw-js

| Capability | Claude | Codex | Impact |
|---|---|---|---|
| Resume/Continue | `--resume <id>` | none | Codex starts fresh every time |
| Model selection | `--model opus/sonnet` | none via maw | Must set in codex config |
| Channel injection | `--channels plugin:discord` | skipped | No Discord bot for Codex |
| System prompt file | `--system-prompt-file` | skipped | Prompts via charter only |
| Process detection | claude, claude-code, thclaude | codex | tmux pane identification |
| Worktree isolation | supported | supported | Both can use `--wt` |

## The Correct Workflow: `maw team up` with Charter

### Charter YAML (from docs/codex-team-pattern.md):
```yaml
name: my-sprint
engines:
  opus: "claude --model opus --dangerously-skip-permissions"
  omx-full: "codex --model gpt-5.5"
members:
  - role: lead
    engine: opus
    worktree: false
  - role: codex-1
    engine: omx-full
    worktree: true
    prompt: "You are codex-1. Task: ..."
```

### Engine Resolution Chain:
```
member.engine ("omx-full")
  → charter.engines["omx-full"]       = "codex --model gpt-5.5"
  → config.engines["omx-full"].cmd     (fallback)
  → config.commands["omx-full"]        (legacy)
  → "omx-full" as raw command          (last resort)
```

### Lifecycle Commands:
```bash
OMX_AUTO_UPDATE=0 maw team up my-sprint        # Spawn
maw peek SESSION:codex-1 --lines 15             # Monitor
maw hey SESSION:codex-1 "new task"              # Send work
maw done codex-1                                 # Graceful shutdown
git worktree prune && mv agents/1-codex-* /tmp/  # Cleanup
```

## What `maw swarm` vs `maw team` Actually Does

| | `maw swarm` | `maw team` |
|---|---|---|
| Config | none | Charter YAML |
| Engine resolution | `resolveEngine()` → bare cmd | Charter engines → config → registry |
| Prompt injection | manual | From charter + queue |
| Worktree | shared cwd | Isolated per member |
| Crash recovery | none | `maw team resume` |
| State tracking | ephemeral | Persistent `~/.claude/teams/` |
| Use case | Quick A/B test | Production work |

## Blockers for Un's Setup

1. **Auth**: `codex doctor` shows ChatGPT OAuth → blocks all models. Fix: `codex login --api-key`
2. **Flag mismatch**: `--dangerously-auto-approve` (old docs) → `--dangerously-bypass-approvals-and-sandbox` (v0.139.0+)
3. **No `--full-auto`**: Codex CLI uses `codex exec -s workspace-write` for non-interactive

## Recent maw-js Changes (Since Last Learn 2026-06-07)

| Commit | Date | Impact |
|---|---|---|
| #2707 dc76b9c9 | 2026-06-11 | Fail-loud on unresolvable engine — prevents silent fallback |
| #2671 961523d9 | 2026-06-10 | Support config.commands without default key |
| #2534 10f65cbe | 2026-06-08 | Charter-local YAML anchor engine aliases |

## Config Changes Made (Un's Machine)

### `~/.config/maw/maw.config.json`:
```json
"commands": {
  "default": "claude",
  "*-oracle": "claude",
  "codex-*": "codex --dangerously-bypass-approvals-and-sandbox"
}
```

### Team Charters Created:
- `.maw/teams/codex-squad.yaml` — Generic claude + 2 codex builders
- `.maw/teams/pops-prototype.yaml` — POPS vet specific, design system rules

---

*Synthesized from 15 deep-explore agents across 3 Soul-Brews-Studio repos | Leica Oracle | 2026-06-11*
