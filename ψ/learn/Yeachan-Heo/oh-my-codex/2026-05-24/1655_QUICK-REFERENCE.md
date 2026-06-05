# oh-my-codex (OMX) — Quick Reference Guide

**Last updated**: 2026-05-24 | **OMX Version**: 0.18.2 | **Node**: >= 20

---

## What It Does

OMX is a **workflow orchestration layer** for OpenAI Codex CLI that makes it easier to:
- Start stronger Codex sessions with better defaults
- Run consistent workflows from clarification to completion
- Keep project guidance, plans, logs, and state organized in `.omx/`
- Coordinate multi-agent teams with durable tmux-backed execution
- Use 30+ agent roles and 40+ skills via natural keywords (e.g., `$architect`, `$deep-interview`)

OMX does NOT replace Codex—it enhances it. Codex is the execution engine; OMX adds the workflow layer.

---

## Installation

### Requirements
- **Node.js 20+** (check: `node --version`)
- **Codex CLI installed & authenticated** (check: `codex --version` and `codex login status`)
- **tmux** on macOS/Linux for team features (optional for single-agent work)
- **psmux** on native Windows (if you want team support)

### Install OMX Globally

**Option 1: If Codex CLI is already installed (Homebrew or npm)**
```bash
npm install -g oh-my-codex
omx setup
```

**Option 2: If you need both Codex and OMX via npm**
```bash
npm install -g @openai/codex oh-my-codex
omx setup
```

**IMPORTANT**: Do NOT reinstall `@openai/codex` with npm if Homebrew already owns `codex` — npm may fail with `EEXIST`. OMX only needs a working `codex` command on PATH.

### Verify Installation
```bash
omx doctor                    # Checks install surface
codex login status            # Checks auth
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"  # Real smoke test
```

---

## Key Features with Examples

### 1. Agent Role Keywords
Use structured roles to invoke specific perspectives on your code:

```bash
omx
# Inside Codex session:
> $architect "analyze the authentication module"
> $security-reviewer "review the API endpoints"  
> $explore "find all database query patterns"
> $executive "summarize the scaling strategy"
```

Each role (architect, security-reviewer, explorer, etc.) comes with pre-baked guidance and prompts.

### 2. Core Workflow: Deep-Interview → Ralplan → Ultragoal

This is the **recommended default workflow**:

```bash
omx --madmax --high   # Launches OMX with optimal concurrency

# In Codex session:
$deep-interview "clarify the authentication change"
# → Explores requirements, boundaries, non-goals, risks

$ralplan "approve the safest implementation path"
# → Creates approved architecture plan with tradeoffs

$prometheus-strict "stress-test the plan before execution"
# (Optional: hardening for high-risk work)

$ultragoal "turn the approved plan into durable Codex goals"
# → Multi-goal execution with `.omx/ultragoal` ledger checkpoints
```

### 3. Skills (Reusable Workflows)

```bash
> /skills                 # Browse all 40+ installed skills

# Research workflows
> $best-practice-research "find upstream evidence for JWT auth"
> $autoresearch "bounded validator-gated research"
> $autoresearch-goal "goal-mode research missions"

# Execution workflows
> $autopilot "build a REST API for task management"
# → Full pipeline: requirements → design → parallel implementation → QA cycling

> $ralph "persistent single-owner completion loop"
# → Alternative to multi-goal (no durable ledger, single focus)

# Team coordination (in Ultragoal stories only)
> $team 3:executor "fix all TypeScript errors"
# → 3 coordinated workers on shared task queue
```

### 4. Wiki for Project Knowledge

Store and retrieve project-specific knowledge:

```bash
omx wiki add "JWT strategy for auth module"        # Add a wiki page
omx wiki query "JWT authentication"                 # Search the wiki
omx wiki list                                       # Browse all pages
omx wiki refresh                                    # Rebuild the index
```

Wiki is markdown-first, search-first (no vectors). Great for onboarding context.

### 5. Team Runtime (Multi-Agent Orchestration)

For work that benefits from parallel workers:

```bash
omx team 5:executor "parallel team smoke test"
# Spawns 5 coordinated agents in tmux with shared task queue

omx team status "team-name"                         # Check health
omx team resume "team-name"                         # Resume after interruption
omx team shutdown "team-name"                       # Graceful cleanup

# Advanced: Team API (JSON interop)
omx team api create-task --input '{...}' --json
omx team api claim-task --input '{...}' --json
omx team api transition-task-status --input '{...}' --json
omx team api send-message --input '{...}' --json
omx team api mailbox-list --input '{...}' --json
```

Mixed-CLI teams (Codex + Claude workers) supported with:
```bash
OMX_TEAM_WORKER_CLI=auto
OMX_TEAM_WORKER_CLI_MAP=codex,codex,codex,claude,claude,claude
omx team 6:executor "task"
```

---

## Configuration Options

### Launch Policies
Control how OMX starts (CLI flags override environment):

```bash
# Managed tmux HUD (default on macOS/Linux)
omx --madmax --high

# Direct launch (no HUD, no tmux management)
omx --direct --yolo

# One-time policy
OMX_LAUNCH_POLICY=direct omx --yolo

# Persistent shell policy
export OMX_LAUNCH_POLICY=tmux|detached-tmux|direct|auto
```

### Environment Variables

```bash
# Auto-update behavior
OMX_AUTO_UPDATE=0                    # Disable launch-time checks
OMX_AUTO_UPDATE=defer                # Schedule update for session exit (no prompt)

# Team runtime
OMX_TEAM_WORKER_CLI=auto|codex|claude              # Worker CLI selection
OMX_TEAM_WORKER_CLI_MAP=codex,codex,claude,claude # Explicit per-worker
OMX_TEAM_WORKER_MCP_COMPAT=1                       # Legacy MCP server compat

# SparkShell (exploration)
OMX_SPARKSHELL_BIN=/path/to/binary                 # Override sidecar
OMX_SPARKSHELL_MODEL=claude-opus-4                 # Override model
OMX_SPARKSHELL_FALLBACK_MODEL=claude-haiku         # Fallback model
OMX_SPARKSHELL_SUMMARY_TIMEOUT_MS=5000             # Timeout for summaries

# Diagnostics
OMX_ROOT=/path/to/omx-home                         # Override .omx location
```

### Config File: `.omx-config.json`

Model/env routing (documented in `docs/reference/omx-config-schema-routing.md`):

```json
{
  "model_context_window": 250000,
  "model_auto_compact_token_limit": 200000,
  "routing": {
    "spark_model": "claude-opus-4",
    "default_model": "claude-opus-4"
  }
}
```

---

## CLI Commands and Usage

### Session Management

```bash
omx                             # Launch with defaults
omx --madmax --high             # Max concurrency + high performance
omx --direct                    # No HUD/tmux management
omx --yolo                      # Trust current state, proceed

omx setup                        # Install prompts, skills, hooks, AGENTS.md
omx setup --merge-agents        # Preserve local AGENTS guidance
omx setup --force               # Overwrite existing AGENTS.md
omx update                       # npm check + reinstall latest + setup

omx doctor                       # Verify install surface
omx doctor --team               # Check team runtime
omx status                       # Check active modes/sessions
omx cancel                       # Cancel any active mode
```

### Exploration

```bash
omx explore --prompt "find where team state is written"
# → Read-only repository lookup (fast, bounded)

omx sparkshell git status
# → Shell-native inspection + summary
omx sparkshell --tmux-pane %12 --tail-lines 400
# → Tail a tmux pane and summarize
```

### Wiki

```bash
omx wiki list --json            # List all pages (JSON)
omx wiki query --input '{"query":"session-start lifecycle"}' --json
omx wiki lint --json            # Check for broken links
omx wiki refresh --json         # Rebuild index
omx wiki add "My learning"      # Add a new page (interactive)
omx wiki delete "page-id"       # Remove a page
```

### Execution & Testing

```bash
omx exec --skip-git-repo-check -C . "Your prompt here"
# → Single execution (no durable state)

omx test:team:cross-rebase-smoke              # Run team integration tests
omx test:recent-bug-regressions               # Regression suite
npm run coverage:team-critical                # Coverage analysis
```

### HUD & Monitoring

```bash
omx hud --watch                 # Monitor/status surface (not user workflow)
```

### API Server (Local Generation)

```bash
omx api                         # Start localhost API gateway for OMX flows
```

---

## How It Compares to Alternatives

### vs Plain Codex CLI
- **Codex alone**: Low-level agent API, no built-in workflow
- **OMX**: Adds 30+ roles, 40+ skills, durable multi-goal coordination, project memory

### vs Other AI Orchestration Tools
- **Durable state**: OMX uses `.omx/` for plans, logs, memory (not ephemeral)
- **tmux-native**: Full team support with shared task queues and claim-safe transitions (no external service)
- **Codex-first**: Tight integration with Codex hooks and native lifecycle (not generic)
- **OMX plugins**: Marketplace integration for plugin discovery + native-hook fallback

### vs Claude Code / Anthropic Codex
- Claude Code uses a different orchestration model (role-driven agents, no multi-goal ledger)
- OMX adds explicit planning + Ultragoal + Rally phases designed for Codex workflows

---

## Recommended Workflow Summary

### For clarification-heavy work:
```
$deep-interview "clarify scope" → $ralplan "approve plan" → $ultragoal "execute"
```

### For autonomous execution:
```
$autopilot "build feature X"
```

### For high-risk changes:
```
$deep-interview "clarify" → $ralplan "approve" → $prometheus-strict "stress-test" 
→ $ultragoal "execute with caution"
```

### For research-first work:
```
$best-practice-research "find evidence" → $ralplan "synthesize findings" 
→ $ultragoal "execute"
```

### For parallel team work:
```
$ultragoal "goal story" → inside story: $team N:role "parallel task"
```

---

## Troubleshooting Quick Fixes

### OMX appears installed but `codex` won't execute
1. Run `codex login status` from the same shell you use for OMX
2. Confirm HOME/CODEX_HOME is where you expect
3. Run real smoke test: `omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"`

### AGENTS.md exists but doctor says OMX contract is missing
```bash
omx setup --scope user --merge-agents   # Restore OMX sections + keep local guidance
```

### Team shows stale state (resume_blocker, missing tmux)
```bash
omx team shutdown <team-name> --force --confirm-issues
omx doctor --team
```

### Shift+Enter submits instead of newline in tmux
This is usually NOT an OMX gap. OMX already enables tmux extended-key forwarding. Check:
- Terminal capability (tmux capabilities: `tmux show -s | grep extended`)
- System terminal app (add to Developer Tools allowlist in macOS Security settings)

### Blue "false-green" doctor but execution fails
Check the active runtime environment (not just your login shell):
```bash
echo $HOME $CODEX_HOME
codex login status
# If using OpenAI-compatible proxy, verify openai_base_url in ~/.codex/config.toml
```

---

## File Inventory

| Component | Count | Location |
|-----------|-------|----------|
| Agent prompts | 30 | `~/.codex/prompts/*.md` |
| Skills | 40 | `~/.codex/skills/*/SKILL.md` |
| MCP servers | 4 | `~/.codex/config.toml` (omx_state, omx_memory, omx_code_intel, omx_trace) |
| CLI commands | 15+ | omx, setup, doctor, team, wiki, explore, sparkshell, exec, api, hud, status, cancel, version, update |
| AGENTS.md | 1 | Project root (generated by setup, preserved with --merge-agents) |
| `.omx/` structure | — | state/, ultragoal/, plans/, logs/, project-memory.json, hooks/ |

---

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS + tmux | Recommended default | High performance, no known issues |
| Linux + tmux | Recommended default | Same experience as macOS |
| Native Windows + psmux | Secondary path | Less tested, supported but inconsistent |
| WSL2 + tmux | Recommended for Windows users | Better than native Windows |
| Codex App (no CLI) | Limited | Use `omx --direct` (no HUD) or launch CLI from shell first |

---

## Resources

- **Official website**: https://yeachan-heo.github.io/oh-my-codex-website/
- **Getting started**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/getting-started.html
- **Agent catalog**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/agents.html
- **Skills reference**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/skills.html
- **Troubleshooting**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/troubleshooting.md
- **Discord community**: https://discord.gg/PUwSMR9XNk
- **GitHub repo**: https://github.com/Yeachan-Heo/oh-my-codex
- **npm package**: https://www.npmjs.com/package/oh-my-codex

---

## License

MIT — Created by Yeachan Heo (@Yeachan-Heo), maintained by HaD0Yun (@HaD0Yun)
