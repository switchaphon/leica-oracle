# oh-my-codex (OMX) Quick Reference Guide

**Version**: 0.18.13 | **Node.js**: ≥20 | **Status**: Production-ready

---

## What is OMX?

oh-my-codex (OMX) is a multi-agent orchestration layer and workflow runtime for OpenAI's Codex CLI. It does **not** replace Codex — rather, it adds a better working layer around it by providing standard workflows (`$deep-interview` → `$ralplan` → `$ultragoal`), durable state management under `.omx/`, specialist roles, and supporting skills. OMX keeps Codex as the execution engine while making it easier to start stronger sessions, run consistent workflows from clarification to completion, manage multi-goal execution, and maintain project guidance through scoped `AGENTS.md` files.

---

## Installation

### Prerequisites
- **Node.js**: 20+
- **Codex CLI**: installed and authenticated (`codex --version` should work)
- **tmux**: macOS/Linux recommended for team runtime (optional)
- **psmux**: Windows-only if you want team runtime support

### Installation Methods

#### Method 1: npm (Recommended)
```bash
npm install -g oh-my-codex
omx setup
omx doctor  # Verify installation
```

#### Method 2: Homebrew (if available)
```bash
brew install oh-my-codex
omx setup
omx doctor
```

#### Method 3: Bun
```bash
bun install -g oh-my-codex
omx setup
omx doctor
```

#### Method 4: Cargo (Rust-based, for advanced users)
```bash
cargo install oh-my-codex
omx setup
omx doctor
```

### First-Time Setup
```bash
omx setup              # Install skills, prompts, config, AGENTS.md
omx doctor            # Check installation health
codex login status    # Verify Codex auth
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"  # Smoke test
```

---

## Core CLI Commands

### Launching OMX

| Command | Purpose |
|---------|---------|
| `omx` | Launch Codex (detached tmux by default) |
| `omx --yolo` | Launch in yolo mode (shorthand for `omx launch --yolo`) |
| `omx --direct` | Launch directly without OMX tmux/HUD management |
| `omx --worktree=<name>` | Launch in a git worktree (safer for `--madmax` sessions) |
| `omx --worktree` | Launch in detached worktree (recommended for one-off work) |
| `omx --high` | High reasoning effort (shorthand: `-c model_reasoning_effort="high"`) |
| `omx --xhigh` | Extra-high reasoning effort (shorthand: `-c model_reasoning_effort="xhigh"`) |
| `omx --madmax` | DANGEROUS: bypass Codex approvals/sandbox (use only with `--worktree` in trusted repos) |
| `omx --madmax-spark` | madmax mode + spark model for workers (`--spark --madmax`) |
| `omx --spark` | Use spark/fast model for team workers only |
| `omx --hotswap` | Rotate auth slots on 429/quota errors and resume |
| `omx --notify-temp` | Enable temporary notification routing for this session only |

### Workflow Commands (In-Session)

| Command | Purpose |
|---------|---------|
| `$deep-interview "..."` | Clarify scope when request/boundaries are vague |
| `$ralplan "..."` | Turn clarified scope into approved architecture/plan |
| `$ultragoal "..."` | Make approved plan durable as sequential goals + ledger |
| `$ralph "..."` | Persistent completion loop (single owner, no multi-goal ledger) |
| `$team "..."` | Coordinated parallel execution (use inside Ultragoal when needed) |
| `/skills` | Browse installed skills and helpers |

### Setup & Configuration

| Command | Purpose |
|---------|---------|
| `omx setup` | Install prompts, skills, AGENTS.md, config |
| `omx setup --merge-agents` | Merge OMX sections into existing `AGENTS.md` |
| `omx setup --scope user` | User-scoped setup (~/.codex) |
| `omx setup --scope project` | Project-scoped setup (./.codex) |
| `omx setup --plugin` | Use Codex plugin delivery (modern path) |
| `omx setup --legacy` | Use legacy setup delivery (backward compat) |
| `omx setup --with-mcp` | Enable MCP compatibility + shared registry sync |
| `omx setup --no-mcp` | Disable MCP (default) |
| `omx setup --force` | Overwrite existing files |
| `omx update` | Check npm, install latest, then refresh setup |
| `omx update --stable` | Install npm stable (@latest), then setup |
| `omx update --dev` | Install upstream dev branch, then setup |
| `omx uninstall` | Remove OMX config and clean up artifacts |
| `omx uninstall --keep-config` | Keep config.toml during uninstall |
| `omx uninstall --purge` | Also remove .omx/ cache directory |

### Execution

| Command | Purpose |
|---------|---------|
| `omx exec <prompt>` | Run codex exec non-interactively with AGENTS overlay |
| `omx exec inject <session-id> --prompt <text>` | Queue follow-up instructions for running exec job |
| `omx imagegen continuation <session-id> --artifact <name>` | Queue image generation continuation |

### Diagnostics & Health

| Command | Purpose |
|---------|---------|
| `omx doctor` | Check installation health (hooks, files, prerequisites) |
| `omx doctor --team` | Check team/swarm runtime health diagnostics |
| `omx cleanup` | Kill orphaned MCP server processes + remove stale /tmp directories |
| `omx status` | Show active modes and state |
| `omx cancel` | Cancel active execution modes |
| `omx reasoning` | Show or set reasoning effort: `omx reasoning <low\|medium\|high\|xhigh>` |

### Session & Resume

| Command | Purpose |
|---------|---------|
| `omx resume` | Resume Codex sessions (supports `--project` + `--codex-home <path>`) |
| `omx ralph` | Launch Codex with ralph persistence mode active |
| `omx session` | Search prior local session transcripts (`--codex-home <path>` escape hatch) |

### Project Guidance

| Command | Purpose |
|---------|---------|
| `omx agents-init [path]` | Bootstrap lightweight `AGENTS.md` files for repo/subtree |
| `omx agents` | Manage Codex native agent TOML files |
| `omx deepinit [path]` | Alias for `agents-init` |

### Team & Multi-Agent

| Command | Purpose |
|---------|---------|
| `omx team <count>:<role> "<task>"` | Spawn parallel worker panes in tmux (e.g., `omx team 3:executor "fix tests"`) |
| `omx team status <team-name>` | Show team status (`--model-inspect` for model inspection) |
| `omx team resume <team-name>` | Resume a paused team |
| `omx team shutdown <team-name>` | Shut down a team (use `--force --confirm-issues` if dead) |
| `omx ultragoal` | Create, resume, checkpoint durable multi-goal plans |
| `omx performance-goal` | Create/gate evaluator-backed performance goals |
| `omx autoresearch-goal` | Create/gate professor-critic research goals |

### Utilities & Advanced

| Command | Purpose |
|---------|---------|
| `omx ask <claude\|gemini>` | Ask local provider and write artifact output |
| `omx adapt` | Scaffold adapter foundations for persistent external targets |
| `omx sparkshell <command> [args...]` | Run native sidecar for direct command execution or tmux summarization |
| `omx sparkshell --tmux-pane <pane-id> [--tail-lines 100-1000]` | Summarize tmux pane |
| `omx api` | Run native omx-api localhost gateway (`serve\|status\|stop\|generate`) |
| `omx wiki` | JSON CLI surface for wiki operations (`list\|query\|lint\|refresh`) |
| `omx hud` | Show HUD statusline (`--watch`, `--json`, `--preset=NAME`) |
| `omx sidecar` | Read-only multi-agent visualization (`--watch`, `--json`, `--tmux`) |
| `omx question` | OMX-owned blocking question UI entrypoint |
| `omx auth` | Manage Codex OAuth auth slots (`add\|list\|use`) |
| `omx list` | List packaged skills + native agent prompts (`--json`) |
| `omx version` | Show version information |
| `omx help` | Show help message |

### Hooks & Internal

| Command | Purpose |
|---------|---------|
| `omx hooks` | Manage hook plugins (`init\|status\|validate\|test`) |
| `omx tmux-hook` | Manage tmux prompt injection workaround (`init\|status\|validate\|test`) |
| `omx mcp-serve` | Launch an OMX stdio MCP server target (plugin/runtime use) |
| `omx state` | Read/write/list OMX mode state via CLI parity surface |

---

## Configuration Files

### File Locations

| Scope | Path | Purpose |
|-------|------|---------|
| User | `~/.codex/.omx-config.json` | User-scoped model/env routing, notifications, wiki config |
| Project | `./.codex/.omx-config.json` | Project-scoped overrides (if `./.omx/setup-scope.json` says `project`) |
| Codex Home | `${CODEX_HOME:-~/.codex}/config.toml` | Codex main config (model, reasoning effort, base URL) |
| Project | `./.codex/config.toml` | Project-scoped Codex config |
| Project | `./.omx/setup-scope.json` | Persists setup scope choice (user or project) |
| Skills | `~/.codex/skills/` (user) or `./.codex/skills/` (project) | OMX skills |
| Prompts | `~/.codex/prompts/` (user) or `./.codex/prompts/` (project) | OMX prompts |
| Agents | `~/.codex/agents/` (user) or `./.codex/agents/` (project) | Codex native agent TOML files |
| Agents Guide | `AGENTS.md` (repo root or `./.codex/`) | Durable orchestration guidance (always persistent) |

### `.omx-config.json` Schema (User/Project Scoped)

```json
{
  "agentReasoning": {
    "architect": "xhigh",
    "critic": "xhigh"
  },
  "env": {
    "OMX_DEFAULT_FRONTIER_MODEL": "gpt-5.5",
    "OMX_DEFAULT_STANDARD_MODEL": "gpt-5.4-mini",
    "OMX_DEFAULT_SPARK_MODEL": "gpt-5.3-codex-spark",
    "OMX_SPARKSHELL_MODEL": "gpt-5.5",
    "OMX_SPARKSHELL_SUMMARY_TIMEOUT_MS": "5000"
  },
  "models": {
    "default": "gpt-5.5",
    "team": "gpt-5.5",
    "team_low_complexity": "gpt-5.3-codex-spark",
    "ralph": "gpt-5.5",
    "autopilot": "gpt-5.5"
  },
  "notifications": {
    "enabled": true,
    "verbosity": "session",
    "discord": {
      "enabled": true,
      "webhook": "https://discordapp.com/api/webhooks/..."
    }
  },
  "wiki": {
    "enabled": true,
    "autoCapture": true,
    "maxContextLines": 500,
    "staleDays": 30
  }
}
```

### `.omx-config.json` Top-Level Keys

| Key | Type | Purpose |
|-----|------|---------|
| `agentReasoning` | Object | Per-agent reasoning overrides (low/medium/high/xhigh) |
| `env` | Object | Fallback environment values for model routing + helpers |
| `models` | Object | Mode-specific model defaults (default, team, team_low_complexity, ralph, etc.) |
| `notifications` | Object | Notification transports, profiles, events, cooldowns, reply settings |
| `wiki` | Object | Project wiki lifecycle (enabled, autoCapture, staleDays, maxPageSize, etc.) |
| `promptRouting` | Object | Triage prompt routing config (`{ "triage": { "enabled": boolean } }`) |
| `autoNudge` | Object | Auto-continuation settings (enabled, patterns, response, delaySec, stallMs) |

### `config.toml` (Codex Main Config)

```toml
[codex]
model = "gpt-5.5"
model_context_window = 250000          # Recommended for OMX
model_auto_compact_token_limit = 200000  # Recommended for OMX
model_reasoning_effort = "medium"      # or: low, high, xhigh
openai_base_url = "https://api.openai.com/v1"  # For custom proxies

[codex.advanced]
# Additional Codex-specific settings
```

---

## OMX vs Codex CLI vs maw

### Relationships

| Tool | Role | Runs | Use When |
|------|------|------|----------|
| **Codex CLI** | Execution engine | Directly invokes OpenAI API | You need agentic AI to complete work |
| **OMX** | Workflow + orchestration layer | Wraps + enhances Codex CLI | You want durable workflows, multi-goal execution, skills, or team coordination |
| **maw** | tmux + orchestration for Oracles | Manages tmux sessions for oracle agents | You're orchestrating multiple AI agents across separate tmux sessions (Father/Mother Oracle pattern) |

### Key Differences

- **Codex CLI alone**: Plain agent without workflow, state management, or skills
- **OMX**: Codex + workflow layer (`$deep-interview` → `$ralplan` → `$ultragoal`) + `.omx/` state + skills + agents overlay + notifications
- **maw**: For Oracle family architecture — manages spawning and messaging between independent Oracle agents in tmux (higher-level pattern than OMX)

OMX is the **right choice** for single-person or team-coordinated work on a single codebase. maw is the **right choice** for orchestrating multiple specialized AI agents with their own long-lived state.

---

## Key Environment Variables

### Model Routing

| Variable | Purpose | Example |
|----------|---------|---------|
| `OMX_DEFAULT_FRONTIER_MODEL` | Main/frontier default for leaders | `gpt-5.5` |
| `OMX_DEFAULT_STANDARD_MODEL` | Optional standard-lane override (inherits frontier if not set) | `gpt-5.4-mini` |
| `OMX_DEFAULT_SPARK_MODEL` | Fast-lane/low-complexity default | `gpt-5.3-codex-spark` |
| `OMX_SPARK_MODEL` | Legacy spark fallback (prefer `OMX_DEFAULT_SPARK_MODEL`) | `gpt-5.3-codex-spark` |
| `OMX_TEAM_CHILD_MODEL` | Team child model (specific paths only) | `gpt-5.4-mini` |

### Launch Policies

| Variable | Values | Purpose |
|----------|--------|---------|
| `OMX_LAUNCH_POLICY` | `auto` (default), `direct`, `tmux`, `detached-tmux` | Controls how OMX launches (detached tmux by default on supported terminals) |
| `OMX_AUTO_UPDATE` | `0` (disable), `defer` (defer without prompt), unset (prompt) | Update check behavior at launch |

### Team & Execution

| Variable | Purpose | Example |
|----------|---------|---------|
| `OMX_TEAM_WORKER_LAUNCH_ARGS` | Worker-specific launch arguments | `-c model_reasoning_effort="low" --model gpt-5.3-codex-spark` |
| `OMX_TEAM_INHERIT_LEADER_FLAGS` | Inherit leader flags for workers | `true` |
| `OMX_TMUX_HUD_OWNER_ENV` | HUD owner pane tracking (internal) | Set by OMX |
| `OMX_TMUX_HUD_LEADER_PANE_ENV` | HUD leader pane ID (internal) | Set by OMX |

### Special Modes

| Variable | Purpose | Example |
|----------|---------|---------|
| `OMX_BYPASS_DEFAULT_SYSTEM_PROMPT` | Skip default system prompt | `true` |
| `OMX_MODEL_INSTRUCTIONS_FILE` | Custom model instructions file | `/path/to/instructions.md` |
| `OMX_RALPH_APPEND_INSTRUCTIONS_FILE` | Ralph mode extra instructions | `/path/to/ralph-instructions.md` |
| `OMX_AUTORESEARCH_APPEND_INSTRUCTIONS_FILE` | Autoresearch extra instructions | `/path/to/research-instructions.md` |
| `OMX_SPARKSHELL_BIN` | Override sparkshell binary path | `/usr/local/bin/omx-sparkshell` |
| `OMX_SPARKSHELL_MODEL` | Sparkshell summary model | `gpt-5.5` |
| `OMX_SPARKSHELL_SUMMARY_TIMEOUT_MS` | Sparkshell timeout | `5000` |

### Codex Auth

| Variable | Purpose |
|----------|---------|
| `CODEX_HOME` | Override Codex home (~/.codex by default) |
| `OPENAI_API_KEY` | OpenAI API key (read by Codex) |

### Internal/Advanced

| Variable | Purpose |
|----------|---------|
| `OMX_STATE_DIR` | Override OMX state directory (./.omx by default) |
| `OMX_NOTIFY_TEMP_CONTRACT_ENV` | Temporary notification routing contract (internal) |
| `DISCORD_STATE_DIR` | Discord bot state directory (./.discord-state by default) |

---

## Launch Flags: `--yolo` vs `--direct`

### `--yolo`
```bash
omx --yolo
```

- Launches Codex in **yolo mode** (skip approval gates, less restrictive)
- Shorthand for: `omx launch --yolo`
- Still runs within OMX's tmux/HUD management (unless `--direct` is also set)
- Use when: You trust the codebase and want fewer approval prompts
- **Note**: Does NOT bypass Codex sandbox. Use `--madmax` to bypass sandbox too.

### `--direct`
```bash
omx --direct
```

- Launches **without OMX tmux/HUD management**
- Runs directly in your current terminal
- If already in a tmux pane, doesn't create HUD splits or enable mouse mode
- Use when: You don't want OMX's visual management overhead
- Useful in: headless/CI environments, minimal terminals, or personal preference

### Combined Usage
```bash
omx --direct --yolo
```
- Run directly in terminal + skip approval gates

### Environment Control
```bash
OMX_LAUNCH_POLICY=direct omx --yolo
OMX_LAUNCH_POLICY=tmux omx --yolo
OMX_LAUNCH_POLICY=auto omx --yolo  # Default
```

- `OMX_LAUNCH_POLICY=auto`: Detached tmux (default on supported terminals), direct otherwise
- `OMX_LAUNCH_POLICY=direct`: Always direct
- `OMX_LAUNCH_POLICY=tmux` or `detached-tmux`: Force managed tmux launch
- CLI flags (`--direct`, `--tmux`) override environment variable

---

## Team Management Commands

### Spawning Teams

```bash
omx team 3:executor "fix the failing tests"     # 3 executor workers
omx team 5:debugger "debug this performance issue"  # 5 debuggers
omx team 2:architect "design the auth system"   # 2 architects
```

**Syntax**: `omx team <count>:<role> "<task>"`

### Team Operations

| Command | Purpose |
|---------|---------|
| `omx team status <team-name>` | Show team status + worker progress |
| `omx team status <team-name> --model-inspect` | Show team status with model inspection hints |
| `omx team resume <team-name>` | Resume a paused team |
| `omx team shutdown <team-name>` | Gracefully shut down a team |
| `omx team shutdown <team-name> --force --confirm-issues` | Force shutdown (for dead teams) |

### Inside an Ultragoal Story

```bash
$team 3:executor "parallel implementation"      # Coordinated team execution
$ralph "continue this until done"              # Single-owner fallback loop
```

### Team Worker Model Arguments

```bash
OMX_TEAM_WORKER_LAUNCH_ARGS='-c model_reasoning_effort="low" --model gpt-5.3-codex-spark' \
  omx team 3:explore "map the config surfaces"
```

### Worker Roles

| Role | Default Model | Use For |
|------|----------------|---------|
| `executor` | Frontier | Primary task execution |
| `debugger` | Standard | Investigation + root cause analysis |
| `architect` | Frontier | Design + architecture decisions |
| `critic` | Frontier | Quality review + consensus gates |
| `explorer` | Spark | Fast exploration + discovery |
| `researcher` | Standard | Investigation + research |
| `writer` | Standard | Documentation + communication |

---

## Resume Workflow

### Session Resume

```bash
omx resume                    # Resume last session
omx resume --project          # Resume within project scope
omx resume --codex-home <path>  # Escape hatch: use specific Codex home
```

Resumes your most recent Codex session with OMX state preserved.

### Ultragoal Resume

```bash
omx ultragoal --resume <ultragoal-id>
```

Resumes a durable multi-goal plan from checkpoint artifacts.

### Ralph Resume

```bash
omx ralph                      # Launch with ralph persistence
```

Ralph mode persists across completion loops, allowing indefinite continuation.

### Session Search

```bash
omx session                    # Search prior transcripts
omx session --codex-home <path>  # Search in specific Codex home
```

Grep through prior local session transcripts.

---

## Doctor/Diagnostics Commands

### Installation Health Check

```bash
omx doctor
```

Verifies:
- OMX files exist and are readable
- Hooks are registered correctly
- Runtime prerequisites (tmux, node, etc.)
- Codex CLI is on PATH and authenticated
- Setup scope (user vs project)
- Codex home and config file locations
- Prompt/skill/agent availability
- Prompt-routing status

**Not checked by `omx doctor`**: Whether active Codex profile can authenticate or run the selected model.

### Team/Swarm Diagnostics

```bash
omx doctor --team
```

Checks:
- Team runtime health
- Stale team processes
- Worktree state
- Worker launch prerequisites

### Troubleshooting False-Green Results

If `omx doctor` passes but execution fails:

```bash
codex login status                    # Check Codex auth
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"  # Smoke test
```

This detects auth, profile, provider/base-URL, and proxy issues that `omx doctor` alone cannot catch.

### Clean Up Stale State

```bash
omx cleanup                                 # Kill orphaned MCP processes
omx team shutdown <team-name> --force --confirm-issues  # Force-close dead team
omx cancel                                  # Cancel active execution modes
```

---

## Plugin System

### Plugin Delivery Models

#### Legacy Mode
- OMX-managed prompts, skills, native agent TOMLs in `~/.codex/` or `./.codex/`
- OMX-managed hooks in `.codex/hooks.json`
- Durable `AGENTS.md` guidance layer

#### Plugin Mode (Modern, Recommended)
- Codex marketplace-delivered plugin bundles bundled skills/hooks
- Plugin cache: `${CODEX_HOME:-~/.codex}/plugins/cache/$MARKETPLACE_NAME/oh-my-codex/$VERSION/`
- Still requires persistent-scope `AGENTS.md` (`./.codex/AGENTS.md` or repo root `AGENTS.md`)
- Hook delivery: `plugins/oh-my-codex/hooks/hooks.json` (plugin-scoped) + fallback `.codex/hooks.json`

### Setup for Plugin Mode

```bash
omx setup --plugin          # Use plugin delivery
omx setup --legacy          # Force legacy delivery
omx setup --install-mode plugin  # Canonical form of --plugin
```

**Plugin Setup Notes**:
- Bundled skills come from plugin cache
- Setup refresh preserves non-OMX entries in `.codex/hooks.json`
- `omx setup --merge-agents` merges OMX sections into existing `AGENTS.md` instead of overwriting
- Without `--merge-agents`, non-interactive setup skips existing `AGENTS.md` files

### Native Hook Mapping

| Path | Scope | Used By |
|------|-------|---------|
| `plugins/oh-my-codex/hooks/hooks.json` | Plugin | Plugin installs (modern) |
| `.codex/hooks.json` | User/project | Legacy installs + fallback |
| `.omx/hooks/*.mjs` | Project | OMX plugin hooks |

### MCP (Model Context Protocol) Configuration

```bash
omx setup --with-mcp      # Enable MCP compatibility + shared registry sync
omx setup --no-mcp        # Disable MCP (default)
omx setup --mcp compat    # Explicit form of --with-mcp
omx setup --mcp none      # Explicit form of --no-mcp
```

**MCP Config**: `.omx-config.json` `notifications` section supports optional MCP compatibility servers and shared registry sync. Disabled by default.

---

## Advanced Usage Patterns

### Cost-Saving Configuration

```json
{
  "env": {
    "OMX_DEFAULT_FRONTIER_MODEL": "gpt-5.5",
    "OMX_DEFAULT_STANDARD_MODEL": "gpt-5.4-mini",
    "OMX_DEFAULT_SPARK_MODEL": "gpt-5.3-codex-spark"
  },
  "models": {
    "default": "gpt-5.4-mini",
    "team": "gpt-5.5",
    "team_low_complexity": "gpt-5.3-codex-spark"
  }
}
```

### Max-Quality Configuration

```json
{
  "agentReasoning": {
    "architect": "xhigh",
    "critic": "xhigh"
  },
  "env": {
    "OMX_DEFAULT_FRONTIER_MODEL": "gpt-5.5",
    "OMX_DEFAULT_SPARK_MODEL": "gpt-5.3-codex-spark"
  },
  "models": {
    "default": "gpt-5.5",
    "team": "gpt-5.5",
    "ralph": "gpt-5.5",
    "team_low_complexity": "gpt-5.3-codex-spark"
  }
}
```

### Worktree Safety Pattern

```bash
# For concurrent --madmax sessions, use distinct named worktrees
omx --worktree=feature/auth --madmax --high
omx --worktree=fix/flaky-tests --madmax --high
```

Never run `--madmax` in the same directory; use named worktrees for isolation.

### Sparkshell Examples

```bash
omx sparkshell git status                    # Direct shell inspection
omx sparkshell --tmux-pane %12 --tail-lines 400  # Summarize tmux pane
```

### Wiki Lifecycle

```json
{
  "wiki": {
    "enabled": true,
    "autoCapture": true,
    "maxContextLines": 500,
    "staleDays": 30,
    "maxPageSize": 10000,
    "feedProjectMemoryOnStart": true
  }
}
```

---

## Recommended Workflow

### Start Here (First Time)

```bash
1. omx setup                # Install skills, prompts, config
2. omx doctor              # Verify installation
3. codex login status      # Check Codex auth
4. omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"  # Smoke test
```

### Main Workflow (Per Task)

```bash
1. omx --worktree=feat/task --high       # Start in isolated worktree with high reasoning
2. $deep-interview "clarify the requirement"  # Clarify scope if needed
3. $ralplan "approve the implementation plan"  # Get architecture + plan
4. $ultragoal "turn the plan into durable goals"  # Execute with checkpoints
```

### For Big Parallel Work

```bash
1. $ultragoal "start the big task"
2. Inside Ultragoal: $team 3:executor "parallel work"  # Spawn team only when needed
3. $ultragoal <continue>                # Come back to checkpoint
```

### End of Session

```bash
omx cancel              # Cancel any active modes
# Exit Codex (Ctrl+D or type 'exit')
```

---

## Configuration Precedence (Model Selection)

### Main/Frontier Default (1st → Last)
1. Shell `OMX_DEFAULT_FRONTIER_MODEL`
2. `.omx-config.json` `env.OMX_DEFAULT_FRONTIER_MODEL`
3. Active Codex `config.toml` root `model`
4. Built-in default: `gpt-5.5`

### Mode-Specific Model (e.g., `team`)
1. `.omx-config.json` `models.team`
2. `.omx-config.json` `models.default`
3. Main/frontier default (above)

### Spark/Low-Complexity Model
1. Shell `OMX_DEFAULT_SPARK_MODEL`
2. Shell legacy `OMX_SPARK_MODEL`
3. `.omx-config.json` `env.OMX_DEFAULT_SPARK_MODEL`
4. `.omx-config.json` `env.OMX_SPARK_MODEL`
5. `.omx-config.json` `models.team_low_complexity`
6. Built-in default: `gpt-5.3-codex-spark`

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `omx doctor` passes but execution fails | Run `codex login status` + `omx exec "test"` from same shell |
| `Shift+Enter` submits instead of newline in tmux | Check tmux terminal capability; OMX enables extended-key forwarding but tmux config may override |
| stale team/resume blocker | `omx team shutdown <name> --force --confirm-issues` + `omx cancel` |
| High `syspolicyd` CPU on Intel Mac | Try `xattr -dr com.apple.quarantine $(which omx)` |
| Custom proxy issues | Verify `~/.codex/config.toml` has correct `openai_base_url` |
| Mixed user/project scope confusion | Run `omx doctor` to see resolved scope + Codex home |

---

## Links & Resources

- **Official Docs**: https://yeachan-heo.github.io/oh-my-codex-website/
- **Getting Started**: https://yeachan-heo.github.io/oh-my-codex-website/getting-started.html
- **Skills Reference**: https://yeachan-heo.github.io/oh-my-codex-website/skills.html
- **Agents Catalog**: https://yeachan-heo.github.io/oh-my-codex-website/agents.html
- **GitHub**: https://github.com/Yeachan-Heo/oh-my-codex
- **Discord Community**: https://discord.gg/sj4exxQ9v
- **npm Package**: https://www.npmjs.com/package/oh-my-codex

---

**Last Updated**: 2026-06-19 | **OMX Version Reference**: 0.18.13
