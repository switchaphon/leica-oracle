# oh-my-codex (OMX) — Quick Reference

**Version**: 0.18.9 | **Language**: TypeScript + Rust | **License**: MIT | **Repository**: https://github.com/Yeachan-Heo/oh-my-codex

---

## What is OMX?

A multi-agent orchestration layer and workflow framework that sits on top of OpenAI Codex CLI. OMX augments Codex with reusable agent roles, parameterized skills, durable state management, and a standardized multi-goal execution pipeline — while Codex remains the core execution engine. Start Codex stronger with better prompts, planning, runtime help, and multi-worker coordination.

**Not a replacement for Codex** — a better working layer around it with standardized workflows, durable state, and team orchestration.

---

## Installation

### Prerequisites
- Node.js 20+
- OpenAI Codex CLI installed and authenticated (`codex --version`)
- Git (recommended)
- `tmux` on macOS/Linux (optional, needed for team mode)

### Install Steps

**If Codex CLI already exists:**
```bash
npm install -g oh-my-codex
omx setup
omx doctor
```

**If Codex CLI does not exist (npm-managed):**
```bash
npm install -g @openai/codex
npm install -g oh-my-codex
omx setup
omx doctor
```

**Do NOT** run both in one command over Homebrew-installed `codex` — npm may fail with `EEXIST`.

### Verify Installation
```bash
omx doctor                    # Checks install shape, prompts, skills, config
codex login status            # Verify auth is configured
omx exec -C . "Reply with exactly OMX-EXEC-OK"  # Smoke test real execution
```

---

## CLI Commands

### Launch Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `omx` | Standard launch in current git repo | `omx` |
| `omx --worktree=<name>` | Launch in isolated git worktree (safer with `--madmax`) | `omx --worktree=feat/task --madmax --high` |
| `omx --madmax` | Bypass approval/sandbox (Codex `--dangerously-bypass-approvals-and-sandbox`) — use only in trusted repos | `omx --madmax` |
| `omx --high` | Set model reasoning effort to "high" (shorthand for `-c model_reasoning_effort="high"`) | `omx --high` |
| `omx --direct` | One-off launch with no tmux/HUD management | `omx --direct --yolo` |
| `omx --yolo` | Skip safety checks | `omx --yolo` |

### Setup & Maintenance

| Command | Purpose |
|---------|---------|
| `omx setup` | Install prompts, skills, config, AGENTS.md, hooks, HUD |
| `omx setup --merge-agents` | Refresh OMX sections in existing AGENTS.md (preserve custom entries) |
| `omx setup --force` | Overwrite existing AGENTS.md and configs |
| `omx update` | Check npm for newer version, install, then run setup |
| `omx doctor` | Verify install shape: Codex CLI, config, prompts, skills, state dirs, MCP servers |
| `omx doctor --team` | Check active tmux teams and workers |
| `omx uninstall` | Remove OMX-managed hooks from `.codex/hooks.json` |

### Status & Lifecycle

| Command | Purpose |
|---------|---------|
| `omx version` | Show OMX version, Node.js, platform |
| `omx status` | Show active modes (e.g., ultragoal, team runs) |
| `omx cancel` | Cancel active modes and clear state |
| `omx exec <prompt>` | Execute a single Codex request (auth + environment smoke test) |
| `omx exec --skip-git-repo-check` | Skip git repo checks in exec |

### Team Commands (Parallel Multi-Agent)

| Command | Purpose | Example |
|---------|---------|---------|
| `omx team <N>:<role>` | Spawn N workers in a tmux team | `omx team 3:executor "fix failing tests"` |
| `omx team status <team-name>` | Show task distribution, worker health, uptime | `omx team status my-team` |
| `omx team resume <team-name>` | Resume a paused/disconnected team | `omx team resume my-team` |
| `omx team shutdown <team-name>` | Graceful team shutdown | `omx team shutdown my-team` |
| `omx team shutdown --force --confirm-issues` | Force-kill dead team | `omx team shutdown my-team --force --confirm-issues` |
| `omx team api <operation>` | Machine-readable JSON API for team operations | `omx team api create-task --input '...' --json` |

### Explore & Research

| Command | Purpose |
|---------|---------|
| `omx explore --prompt "..."` | Read-only codebase discovery (low cost) |
| `omx sparkshell <command>` | Shell-native inspection + bounded summarization |
| `omx sparkshell --tmux-pane %N` | Inspect a specific tmux pane's tail |

### Wiki (Project Knowledge)

| Command | Purpose |
|---------|---------|
| `omx wiki list --json` | List all wiki entries |
| `omx wiki query --input '{"query":"..."}' --json` | Search wiki |
| `omx wiki lint --json` | Validate wiki integrity |
| `omx wiki refresh --json` | Rebuild wiki search index |

### Hooks & HUD

| Command | Purpose |
|---------|---------|
| `omx hud --watch` | Monitor/status surface (not the main workflow) |
| `omx tmux-hook` | Called by Codex native hooks on session lifecycle events |

---

## Core Workflow Skills

These are the main in-session workflows. Use them in order inside a Codex session.

### 1. `$deep-interview`
- **When**: Clarify intent, scope, and non-goals when unclear
- **Input**: User's vague or complex request
- **Output**: Clarified scope, boundaries, acceptance criteria
- **Example**: `$deep-interview "clarify the authentication change"`

### 2. `$ralplan`
- **When**: Turn clarified scope into an approved architecture and implementation plan
- **Input**: Clarified scope or requirements
- **Output**: Durable plan artifact, tradeoff analysis, architecture decision record
- **Example**: `$ralplan "approve the safest implementation path"`
- **Note**: Stops at planning — does not implement code

### 3. `$ultragoal`
- **When**: Execute the approved plan with durable multi-goal checkpoints and ledger
- **Input**: Approved plan from `$ralplan`
- **Output**: Implemented code, `.omx/ultragoal` ledger with completed story IDs
- **Example**: `$ultragoal "turn the approved path into durable Codex goals"`
- **Use inside ultragoal**: `$team` for coordinated parallel stories or `$ralph` for persistent single-owner loop

### 4. `$code-review`
- **When**: Review executed code for correctness, maintainability, security
- **Input**: Code changes from execution
- **Output**: Findings, remediation code examples
- **Example**: `$code-review "review the auth changes"`

### 5. `$ultraqa`
- **When**: Comprehensive QA after code review (interactive, staged, multi-perspective)
- **Input**: Reviewed code
- **Output**: QA pass/fail, blocked issues, regression coverage
- **Example**: `$ultraqa "validate the auth feature end-to-end"`

---

## Advanced Skills

### Research

| Skill | Purpose | When to use |
|-------|---------|------------|
| `$best-practice-research` | Official upstream evidence for ordinary planning | Pre-planning architecture decisions |
| `$autoresearch` | Bounded validator-gated research artifacts | When you need cited research without hallucination risk |
| `$autoresearch-goal` | Goal-mode research missions | Turn research into durable multi-step goals |

### Execution

| Skill | Purpose | When to use |
|-------|---------|------------|
| `$team` | Coordinated parallel work within an Ultragoal story | When one story benefits from multi-worker parallelism |
| `$ralph` | Persistent single-owner completion loop (legacy alternate to Ultragoal) | When you do NOT need multi-goal ledger; intentional fallback |
| `$autopilot` | Strict autonomous loop: interview → plan → execute → review → QA → iterate | Hands-off delivery from idea to reviewed, QA-checked code |

### Other Workflow Skills

| Skill | Purpose |
|-------|---------|
| `$review` | Code review surface (post-execution artifact review) |
| `$security-review` | OWASP Top 10 analysis with severity prioritization |
| `$tdd` | Test-driven development loop |
| `$build-fix` | Build/toolchain/type error resolution |
| `$design` | UI/UX architecture and interaction design |
| `$pipeline` | CI/CD pipeline analysis and hardening |
| `$analyze` | Requirements and acceptance criteria clarification |
| `$help` | Skill discovery and onboarding |
| `$cancel` | Cancel active mode and reset state |
| `$note` | Inline note-taking in workflow |
| `$hud` | Status monitoring surface |
| `$configure-notifications` | Set up notification hooks (OpenClaw, Discord, etc.) |

---

## Available Agent Roles

OMX ships with 30+ agent prompts. Use role keywords as `$<role-name>` inside Codex.

### Core Roles (Build & Analysis)
- **explore** — Codebase discovery, symbol mapping (low cost)
- **analyst** — Requirements clarification, acceptance criteria
- **planner** — Execution plans, sequencing, dependency analysis
- **architect** — System design, service boundaries, trade-off analysis
- **debugger** — Root-cause diagnosis, regression investigation
- **executor** — Implementation, refactoring (medium reasoning)
- **verifier** — Evidence-backed completion checks

### Review Roles
- **style-reviewer** — Formatting, naming conventions (low cost)
- **quality-reviewer** — Logic defects, maintainability
- **api-reviewer** — API contracts, backward compatibility
- **security-reviewer** — Security boundaries, vulnerabilities (OWASP Top 10)
- **performance-reviewer** — Performance bottlenecks, algorithmic complexity
- **code-reviewer** — Comprehensive multi-axis review (high reasoning)

### Domain Specialists
- **dependency-expert** — SDK/API/package evaluation and comparison
- **test-engineer** — Test strategy, coverage planning
- **quality-strategist** — Release quality and risk assessment
- **build-fixer** — CI, toolchain, type issue resolution
- **designer** — UI/UX architecture, interaction design
- **writer** — Documentation, migration guides
- **qa-tester** — Interactive manual QA validation
- **git-master** — Commit strategy, history hygiene
- **researcher** — Official API docs, reference collection

### Product Roles
- **product-manager** — PRD definition, user outcome framing
- **ux-researcher** — Heuristic usability audits, accessibility
- **information-architect** — Navigation, taxonomy, structure
- **product-analyst** — Metrics, funnels, experiment design

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OMX_LAUNCH_POLICY` | `auto` | Launch mode: `direct`, `tmux`, `detached-tmux`, `auto` |
| `OMX_AUTO_UPDATE` | Throttled prompt | `0` = disable, `defer` = schedule silently, or unset for prompt |
| `OMX_BYPASS_DEFAULT_SYSTEM_PROMPT` | `0` | Skip layering `AGENTS.md` instructions |
| `OMX_MODEL_INSTRUCTIONS_FILE` | `<cwd>/AGENTS.md` | Custom project instructions file |
| `OMX_SPARKSHELL_BIN` | Auto-detect | Native sidecar binary for sparkshell |
| `OMX_SPARKSHELL_MODEL` | gpt-4o-mini | Primary summary model for `omx explore` |
| `OMX_SPARKSHELL_FALLBACK_MODEL` | gpt-4-turbo | Fallback model if primary times out |
| `OMX_SPARKSHELL_SUMMARY_TIMEOUT_MS` | 5000 | Local API summary timeout |

### Config File: `.codex/config.toml`

OMX setup writes/updates this file with:
- **MCP servers** — omx_state, omx_memory, omx_code_intel, omx_trace
- **Model config** — gpt-5.5 recommendations: `model_context_window = 250000`, `model_auto_compact_token_limit = 200000`
- **Hooks** — Codex native lifecycle hooks for OMX (plugin-scoped or legacy `.codex/hooks.json`)
- **TUI status line** — HUD/monitoring configuration via `[tui]` section

### Project Instructions: `AGENTS.md`

Generated per-project, layered into Codex session at launch (via `-c model_instructions_file=...`):
- Delegation rules and team compositions
- 30-agent catalog with descriptions
- 40+ skill descriptions and trigger patterns
- Model routing guidance (complexity-based)
- Verification protocols

Use `--merge-agents` during setup to preserve custom sections:
```bash
omx setup --merge-agents
```

### Durable State: `.omx/`

OMX stores plans, logs, memory, and mode tracking under `.omx/`:
- `.omx/state/` — Runtime state files
- `.omx/ultragoal/` — Completed story IDs, ledger checkpoints
- `.omx/plans/` — Planning artifacts (design docs, architecture decisions)
- `.omx/team/` — Team session state, worker identity, task queues
- `.omx/hooks/` — Plugin-scoped hooks (`.mjs` files)
- `.omx-config.json` — Model/env routing (see `docs/reference/omx-config-schema-routing.md`)

---

## Tech Stack Summary

### Language & Build
- **Primary**: TypeScript (Node.js 20+)
- **Compiler**: tsc (TypeScript compiler)
- **Linter**: Biome (modern Rust-powered linter)

### Rust Crates (Native Performance)
- **omx-api** — API server and team coordination
- **omx-explore** — Codebase indexing and symbol discovery (faster than pure JS)
- **omx-mux** — Terminal multiplexing abstractions
- **omx-runtime-core** — Core Codex runtime state machine
- **omx-runtime** — Full Codex runtime orchestrator
- **omx-sparkshell** — Shell-native inspection + summarization

### MCP (Model Context Protocol)
- **omx_state** — Runtime state access (MCP server)
- **omx_memory** — Project memory and long-term context (MCP server)
- **omx_code_intel** — Code intelligence, symbol lookup (MCP server)
- **omx_trace** — Execution trace and audit logging (MCP server)

### Dependencies
- **@modelcontextprotocol/sdk** — MCP protocol implementation
- **@iarna/toml** — TOML config parsing
- **zod** — TypeScript-first schema validation

### Testing & Coverage
- **Node native test runner** — Built-in assertion module
- **c8** — Code coverage (lines, branches, functions, statements)
- **Cargo test** — Rust crate unit tests

---

## How OMX Compares to Similar Tools

### vs. Plain Codex CLI
- **Codex**: Powerful agent execution engine, requires manual setup for each session
- **OMX**: Codex + reusable roles + durable workflow + standardized skills + team coordination
- **OMX advantage**: Faster onboarding, repeatable workflows, multi-goal execution, durable state

### vs. Other AI CLI Wrappers
- **Aider** (LLM-powered code editing): Single-file focused, not multi-agent orchestration
- **Continue** (VS Code plugin): IDE-embedded, not CLI-first
- **OMX**: CLI-first, OpenAI Codex-specific, multi-agent orchestration, durable team mode

### vs. General-Purpose Agent Frameworks (e.g., LangChain, Crew.AI)
- **General frameworks**: Flexible, language-agnostic, steep learning curve
- **OMX**: Purpose-built for Codex workflows, opinionated (in a good way), faster to productive use
- **OMX advantage**: Canonical workflow (`interview → plan → execute → review → QA`), project-scoped AGENTS.md, durable multi-goal ledger

### Key Differentiators
1. **Codex-native** — Tight integration with OpenAI Codex CLI (not generic LLM wrappers)
2. **Durable state** — Plans, logs, memories, team state persist in `.omx/` across sessions
3. **Canonical workflow** — Proven interview → plan → execute → review → QA → iterate loop
4. **Claim-safe team mode** — Multiple workers coordinate via versioned task claims and mailbox messaging
5. **MCP servers** — First-class runtime state, code intelligence, trace logging
6. **Project-scoped guidance** — AGENTS.md acts as orchestration brain, customizable per project

---

## Quick Start Checklist

1. ✅ Install Codex CLI: `npm install -g @openai/codex` (or use Homebrew)
2. ✅ Install OMX: `npm install -g oh-my-codex`
3. ✅ Setup: `omx setup`
4. ✅ Verify: `omx doctor`
5. ✅ Smoke test: `codex login status` + `omx exec -C . "Reply with exactly OMX-EXEC-OK"`
6. ✅ First launch: `omx --worktree=feat/task --madmax --high`
7. ✅ Core workflow:
   - `$deep-interview "clarify the request"`
   - `$ralplan "approve the plan"`
   - `$ultragoal "execute with durable checkpoints"`
   - `$code-review` (if needed)
   - `$ultraqa` (final validation)

---

## Resources

- **Official Docs**: https://yeachan-heo.github.io/oh-my-codex-website/
- **Getting Started**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/getting-started.html
- **Agent Catalog**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/agents.html
- **Skills Reference**: https://github.com/Yeachan-Heo/oh-my-codex/blob/main/docs/skills.html
- **Discord Community**: https://discord.gg/sj4exxQ9v
- **GitHub Issues**: https://github.com/Yeachan-Heo/oh-my-codex/issues

---

**Last updated**: 2026-06-06  
**Maintained by**: Yeachan Heo and maintainers (Doyun Ha, Valeriy Pavlovich)  
**License**: MIT
