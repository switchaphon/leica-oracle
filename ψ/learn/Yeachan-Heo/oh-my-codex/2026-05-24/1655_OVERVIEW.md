# oh-my-codex (OMX) — Overview

## What It Is

**oh-my-codex** (OMX) is a workflow orchestration layer for [OpenAI Codex CLI](https://github.com/openai/codex). It does NOT replace Codex — it wraps around it to provide structured workflows, multi-agent team coordination, and durable state management.

Think of it as: **"oh-my-zsh but for OpenAI Codex"** — enhances the vanilla CLI with roles, skills, and workflow patterns.

**Version**: 0.18.2
**Author**: Yeachan Heo (Korean developer)
**License**: MIT
**npm**: `oh-my-codex`

## Architecture

### Dual Runtime: TypeScript + Rust

| Layer | Language | Role |
|-------|----------|------|
| CLI + Orchestration | TypeScript (Node 20+) | Main CLI (`omx`), team management, hooks, HUD, state |
| Performance paths | Rust (6 crates) | explore, sparkshell, mux, runtime, API server |

### Rust Crates

```
crates/
├── omx-api/          # HTTP API server
├── omx-explore/      # Fast codebase exploration
├── omx-mux/          # tmux multiplexer control
├── omx-runtime-core/ # Core runtime primitives
├── omx-runtime/      # Full runtime implementation
└── omx-sparkshell/   # Shell inspection + summarization
```

### TypeScript Modules

```
src/
├── cli/              # CLI entry point (omx command)
├── team/             # Multi-agent team coordination (tmux-based)
├── hooks/            # Codex lifecycle hooks
├── hud/              # Heads-Up Display (status monitoring)
├── mcp/              # MCP server integration
├── ralph/            # Persistent completion loops
├── exec/             # Command execution
├── goal-workflows/   # Ultragoal durable multi-goal system
├── autoresearch/     # Bounded research with validators
├── agents/           # Agent role definitions
├── adapt/            # Adaptive behavior
├── config/           # Configuration management
├── notifications/    # Notification system (Discord, OpenClaw)
├── openclaw/         # OpenClaw notification gateway
├── modes/            # Mode tracking (madmax, high, etc.)
└── pipeline/         # CI/CD pipeline integration
```

## Core Workflow

The canonical OMX workflow is a 3-step pipeline:

```
$deep-interview → $ralplan → $ultragoal
```

1. **$deep-interview** — Clarify scope, boundaries, non-goals (interview-style)
2. **$ralplan** — Approve architecture + implementation plan with tradeoffs
3. **$ultragoal** — Convert approved plan into durable sequential Codex goals

Optional:
- **$prometheus-strict** — Stress-test plans before execution (interview/critique/synthesis)
- **$team** — Coordinated parallel execution (tmux-based multi-agent)
- **$ralph** — Single-owner persistent completion loop

## Agent Roles (prompts/)

OMX ships with pre-built agent role prompts:

| Role | File |
|------|------|
| architect | prompts/architect.md |
| executor | prompts/executor.md |
| code-reviewer | prompts/code-reviewer.md |
| debugger | prompts/debugger.md |
| test-engineer | prompts/test-engineer.md |
| security-reviewer | prompts/security-reviewer.md |
| designer | prompts/designer.md |
| writer | prompts/writer.md |
| analyst | prompts/analyst.md |
| team-orchestrator | prompts/team-orchestrator.md |
| verifier | prompts/verifier.md |
| build-fixer | prompts/build-fixer.md |

## Skills System

```
skills/
├── ralplan/          # Architecture planning
├── ultragoal/        # Durable goal management
├── review/           # Code review
├── tdd/              # Test-driven development
├── autopilot/        # Autonomous execution
├── security-review/  # Security audit
├── frontend-ui-ux/   # UI/UX design
├── performance-goal/ # Performance optimization
├── design/           # System design
├── pipeline/         # CI/CD pipeline
├── hud/              # HUD management
├── worker/           # Worker agent
├── ecomode/          # Token-efficient mode
├── note/             # Note taking
├── build-fix/        # Build error fixing
└── cancel/           # Cancel operations
```

## Team Runtime

Multi-agent via **tmux** (macOS/Linux) or **psmux** (Windows):

```bash
omx team 3:executor "fix the failing tests"
omx team status <team-name>
omx team resume <team-name>
omx team shutdown <team-name>
```

Each team member runs in its own tmux pane with a specific role prompt.

## State Management

All persistent state lives in `.omx/`:
- Plans
- Logs
- Memory
- Mode tracking
- Ultragoal ledger/checkpoints
- Wiki (markdown-first, search-first)

## Key Commands

```bash
omx setup                  # Install prompts, skills, AGENTS.md, hooks
omx doctor                 # Verify install health
omx --madmax --high        # Launch with maximum capability
omx --direct --yolo        # Direct launch, no tmux
omx explore --prompt "..." # Read-only repo lookup
omx sparkshell <cmd>       # Shell inspection
omx wiki list              # Wiki operations
omx hud --watch            # Status monitoring
omx exec "..."             # Direct execution
omx update                 # Check + install latest
```

## Dependencies

Minimal:
- Runtime: `@iarna/toml`, `@modelcontextprotocol/sdk`, `zod`
- Dev: `typescript`, `biome`, `c8`
- System: `tmux`, `codex` CLI, Node.js 20+

## Comparison to Oracle System

| Aspect | OMX | Oracle (our system) |
|--------|-----|---------------------|
| Target AI | OpenAI Codex CLI | Claude Code |
| Architecture | Wrapper around single AI tool | Full distributed AI family |
| State | `.omx/` directory | `ψ/` brain structure |
| Multi-agent | tmux panes with role prompts | Full Oracle repos with own identity |
| Skills | SKILL.md files | `/skill` commands |
| Workflow | $deep-interview → $ralplan → $ultragoal | /learn → /trace → /rrr |
| Identity | Roles (executor, reviewer) | Named Oracles (Leica, Codec, Neon) |
| Communication | tmux stdin/stdout | maw federation + Discord |
