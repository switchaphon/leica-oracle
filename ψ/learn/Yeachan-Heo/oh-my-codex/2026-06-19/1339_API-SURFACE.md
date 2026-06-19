# oh-my-codex (OMX) — API Surface & Integration Reference

**Date:** 2026-06-19  
**Version:** 0.18.13  
**Scope:** Complete API surface, CLI commands, plugin/extension points, integration layer with Codex CLI and maw

---

## Executive Summary

OMX is a **workflow orchestration layer** for Codex CLI, not a replacement. It:
- Wraps Codex CLI with better task routing, planning, multi-agent coordination, and runtime state management
- Provides a durable multi-goal execution model (`$ultragoal`, `$ralph`, `$team`) above Codex's single-session model
- Integrates with Codex via **native hooks** (codex-native-hook.ts) and an optional **Codex plugin layout** (plugins/oh-my-codex/)
- Delivers reusable workflows as **skills** (via prompts in user/project `.codex/skills` or plugin-bundled)
- Manages runtime state under `.omx/` with **MCP servers** for structured access from Codex
- Supports **team/swarm coordination** through tmux with persistent worker state and checkpoints

### Key Design Principles

1. **Codex remains the execution engine** — OMX adds routing, state, and workflow above it
2. **Plugin-first delivery** — Modern installs use Codex plugin discovery; legacy setups use `omx setup`
3. **Persistent state under `.omx/`** — Plans, logs, team state, skill activation, mode tracking all durable
4. **Native Codex hooks** — Pre/PostToolUse, UserPromptSubmit, SessionStart, Stop gates allow OMX runtime visibility
5. **MCP for structured access** — `omx_wiki`, `omx_memory`, `omx_state`, `omx_code_intel`, `omx_trace` servers expose durable state to Codex

---

## 1. CLI Commands & Signatures

### Main Entry Point

```bash
omx [command] [options] [--]
```

The binary is at `dist/cli/omx.js` after build. Entry point in src: `src/cli/index.ts`.

### Core Commands

#### Launch & Execution

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `omx` (no args) | Launch interactive Codex (default: detached tmux on macOS/Linux) | `--direct`, `--tmux`, `--yolo`, `--madmax`, `--high`, `--xhigh`, `-w/--worktree[=name]` |
| `omx exec <prompt>` | Non-interactive Codex execution with OMX overlay injection | `--skip-git-repo-check`, `-C <dir>`, `--madmax`, `--high` |
| `omx exec inject <session-id> --prompt <text>` | Queue follow-up instructions for running exec job | `--prompt`, `--session-id` |
| `omx launch` | Explicit launch (same as `omx` with no args) | Same as `omx` |

#### Planning & Execution Modes

| Command | Purpose | Behavior |
|---------|---------|----------|
| `omx deep-interview` | Socratic clarification (skill) | Gated ambiguity scoring; writes `.omx/context/` snapshot; hands off to planning |
| `omx ralplan` | Architecture & plan approval (skill) | Builds durable plan artifact; requires explicit approval before `$ultragoal` execution |
| `omx ultragoal` | Durable multi-goal completion | Checkpoints in `.omx/ultragoal/`; goal-ledger state in `.omx/state/` |
| `omx ralph` | Persistent single-owner loop | Ralph mode execution; tracks completion in `.omx/state/ralph/` |
| `omx team <count>:<role> <task>` | Parallel multi-worker execution | Spawns tmux panes; workers report to leader; persistent state in `.omx/state/team/` |
| `omx autoresearch` (deprecated) | Bounded research missions | Use `$autoresearch` skill instead; CLI launch removed |

#### Setup & Maintenance

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `omx setup` | Install prompts, skills, hooks, `.codex/config.toml`, AGENTS.md | `--scope user/project`, `--legacy`, `--plugin`, `--mcp none/compat`, `--merge-agents`, `--force` |
| `omx update` | Install stable npm version, then refresh setup | `--stable`, `--dev` |
| `omx uninstall` | Remove OMX configuration | `--keep-config`, `--purge` |
| `omx doctor` | Verify installation health | `--team` (check team runtime), `--verbose` |
| `omx cleanup` | Kill orphaned MCP processes, remove stale `/tmp` dirs | (no key options) |

#### Runtime Management

| Command | Purpose |
|---------|---------|
| `omx list` | List installed skills and native agents (`--json`) |
| `omx agents` | Manage native Codex agent TOML files |
| `omx agents-init [path]` | Bootstrap lightweight AGENTS.md |
| `omx auth add/list/use` | Manage OAuth auth slots (for quota rotation) |
| `omx ask` | Ask local provider (claude/gemini) and write artifact |
| `omx question` | OMX-owned blocking question UI (internal) |
| `omx status` | Show active modes and state |
| `omx cancel` | Cancel active execution modes |
| `omx reasoning <low\|medium\|high\|xhigh>` | Show or set model reasoning effort |

#### MCP & State Access

| Command | Purpose | Format |
|---------|---------|--------|
| `omx state read/write/list` | CLI parity for OMX mode state | `--input '<json>'`, `--json` |
| `omx wiki list/query/lint` | Wiki operations | `--json`, `--input '<json>'` |
| `omx trace` | Trace operations (MCP compatibility) | `--json` |
| `omx code-intel` | Code intelligence queries | `--json` |
| `omx notepad` | JSON notepad operations | `--json` |
| `omx project-memory` | JSON project memory operations | `--json` |
| `omx mcp-serve` | Launch stdio MCP server | `--stdio` (default) |

#### Monitoring & Utilities

| Command | Purpose |
|---------|---------|
| `omx hud --watch` | HUD statusline (monitoring surface) |
| `omx sidecar --watch` | Team/multi-agent visualization |
| `omx sparkshell <cmd>` | Shell-native inspection sidecar |
| `omx sparkshell --tmux-pane %N` | Summarize tmux pane |
| `omx session --codex-home <path>` | Search prior session transcripts |
| `omx tmux-hook init/status/test` | Manage tmux prompt injection workaround |
| `omx hooks init/status/test` | Manage hook plugins |
| `omx api serve/status/stop` | Native omx-api localhost gateway |

#### Other

| Command | Purpose |
|---------|---------|
| `omx help` | Show full help |
| `omx version` | Show version + build info |
| `omx adapt` | Scaffold adapter foundations for persistent external targets |

### Shorthand Options

| Flag | Expands To | Effect |
|------|-----------|--------|
| `--madmax` | `--dangerously-bypass-approvals-and-sandbox` | Bypass Codex approval gates (dangerous; use only in trusted repos) |
| `--spark` | Worker model = low-complexity spark model | Leader unchanged |
| `--madmax-spark` | `--spark --madmax` | Spark workers + approval bypass |
| `--high` | `-c model_reasoning_effort="high"` | High reasoning effort |
| `--xhigh` | `-c model_reasoning_effort="xhigh"` | Extra-high reasoning effort |
| `--yolo` | Unsafe fast execution | Minimal guardrails |
| `--hotswap` | Auth slot rotation on 429/quota errors | Resume on 429 errors |
| `--notify-temp` | Temporary notification routing | Requires `--discord`, `--slack`, `--telegram`, or `--custom <name>` |

### Environment Variables

| Env Var | Purpose | Example |
|---------|---------|---------|
| `OMX_LAUNCH_POLICY` | Default launch behavior | `auto`, `direct`, `tmux`, `detached-tmux` |
| `OMX_AUTO_UPDATE` | Launch-time update check | `0` (disable), `defer` (schedule without prompt), (default: prompt) |
| `OMX_SPARKSHELL_BIN` | Path to sparkshell sidecar | `/custom/path/to/sparkshell` |
| `OMX_SPARKSHELL_MODEL` | Summary model for sparkshell | (inherits from Codex config) |
| `OMX_TEAM_WORKER_LAUNCH_ARGS` | Worker model/args override | `--model claude-opus-4-8` |
| `OMX_DEFAULT_SPARK_MODEL` | Low-complexity team worker model | `claude-opus-4-8` (default if not set) |
| `OMX_DEFAULT_FRONTIER_MODEL` | High-complexity team leader model | `claude-opus-4-8` (default if not set) |
| `OMX_QUESTION_RETURN_PANE` | Tmux pane to return to after `omx question` | `%12` (for deep-interview) |
| `CODEX_HOME` | Codex config directory | `~/.codex` (default) |
| `OMX_STATE_VERBOSE` | Debug state transitions | `1` |

---

## 2. Plugin System & Codex Integration

### Plugin Layout

OMX ships a **Codex plugin layout** at `plugins/oh-my-codex/` with:

```
plugins/oh-my-codex/
├── hooks/
│   └── hooks.json                    # Plugin-scoped hook registrations
├── skills/                           # Bundled skill SKILL.md files
│   ├── deep-interview/SKILL.md
│   ├── ralplan/SKILL.md
│   ├── ultragoal/SKILL.md
│   ├── team/SKILL.md
│   ├── ask/SKILL.md
│   └── ... (20+ skills)
├── agents/                           # Plugin-scoped agent prompts
│   └── ... (role prompts)
└── .agents/
    └── plugins/
        └── marketplace.json          # Codex marketplace metadata
```

### Plugin vs. Legacy Setup

**Plugin Mode (Recommended):**
- Codex discovers OMX from Codex plugin marketplace or local cache
- Plugin cache: `${CODEX_HOME:-~/.codex}/plugins/cache/$MARKETPLACE_NAME/oh-my-codex/$VERSION/`
- Skills bundled in plugin; native hooks from plugin-scoped `hooks.json`
- Persistent scope `AGENTS.md` still required (either `~/.codex/AGENTS.md` or `./AGENTS.md`)
- Installed `omx` CLI executes plugin hooks at runtime

**Legacy Mode:**
- `omx setup` writes OMX-managed hooks to `.codex/hooks.json`
- Skills copied to `~/.codex/skills/` or `./.codex/skills/`
- Prompts copied to `~/.codex/prompts/` or `./.codex/prompts/`
- AGENTS.md installed at user or project scope

### Hook Integration

**Native Codex Hooks:** OMX registers as a Codex hook to intercept key lifecycle events.

**Hookable Events:**

| Event | Signature | OMX Handler | Purpose |
|-------|-----------|-------------|---------|
| `SessionStart` | `(context: SessionStartContext)` | `codex-native-hook SessionStart ...` | Initialize session state, skill activation, mode detection |
| `UserPromptSubmit` | `(prompt: string, context: ...)` | `codex-native-hook UserPromptSubmit ...` | Detect skills, keywords; inject routing overlay; triage; reconcile HUD |
| `PreToolUse` | `(tool: ToolCall, context: ...)` | `codex-native-hook PreToolUse ...` | Detect MCP transport failures; inject pre-tool guidance |
| `PostToolUse` | `(result: ToolResult, context: ...)` | `codex-native-hook PostToolUse ...` | Handle team worker notifications; nudge leader; auto-nudge for stalls |
| `PreCompact` | `(compactContext: ...)` | `codex-native-hook PreCompact ...` | Build wiki context; snapshot session state |
| `PostCompact` | `(outcome: CompactOutcome)` | `codex-native-hook PostCompact ...` | (unused in current builds) |
| `Stop` | `(stopContext: StopContext)` | `codex-native-hook Stop ...` | Gate skill stops; transition mode state; trigger `ralph` resume if needed |

**Hook Registration:**

```json
{
  "hooks": [
    {
      "event": "SessionStart",
      "target": "omx hook native SessionStart"
    },
    {
      "event": "UserPromptSubmit",
      "target": "omx hook native UserPromptSubmit"
    }
  ]
}
```

### Hook Entry Point

**File:** `src/scripts/codex-native-hook.ts`  
**Compiled to:** `dist/scripts/codex-native-hook.js`

**Invocation:**
```bash
node dist/scripts/codex-native-hook.js <event-name> --json '<hook-payload>'
```

**Event Names:**
- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PreCompact`
- `Stop`

**Payload Format:** Codex hook JSON payload (varies by event).

**Return Format:** JSON with:
```json
{
  "hookEventName": "SessionStart" | "UserPromptSubmit" | ... | null,
  "omxEventName": "deep_interview_active" | ... | null,
  "skillState": { "activeSkill": "...", ... } | null,
  "outputJson": { "instruction": "...", ... } | null
}
```

---

## 3. Skills System

### Skill Delivery

Skills are distributed as **Markdown files** (`.md`) containing:
- YAML frontmatter with name, description, and hints
- Structured execution policy + workflow steps
- Keyword detection for auto-routing

### Skill Locations

**Plugin Mode:**
- `${CODEX_HOME:-~/.codex}/plugins/cache/oh-my-codex/$VERSION/skills/*/SKILL.md`

**Legacy Mode:**
- User scope: `~/.codex/skills/*/SKILL.md`
- Project scope: `./.codex/skills/*/SKILL.md`

### Core Skill Catalog

| Skill | Purpose | Invocation |
|-------|---------|-----------|
| `deep-interview` | Socratic clarification loop (3 depth profiles) | `$deep-interview "your request"` |
| `ralplan` | Architecture review & consensus building | `$ralplan "review and approve the plan"` |
| `ultragoal` | Durable multi-goal execution with checkpoints | `$ultragoal "turn plan into durable goals"` |
| `ralph` | Persistent single-owner completion loop | `$ralph "complete and verify"` |
| `team` | Parallel multi-worker orchestration | `$team 3:executor "task"` |
| `ask` | Query local provider (claude/gemini) | `$ask "question"` |
| `autoresearch` | Bounded research missions | `$autoresearch --mission "research task"` |
| `design` | Design-system and component guidance | `$design "design question"` |
| `plan` | Lightweight planning (no interview) | `$plan "outline plan"` |
| `skill` | Skill creation and scaffolding | `$skill create "skill-name"` |
| `pipeline` | Pipeline coordination for sequences | `$pipeline "coordinate workflow"` |
| `cancel` | Cancel active modes | `$cancel` |

### Skill Metadata (YAML Frontmatter)

```yaml
---
name: skill-slug
description: One-line description
argument-hint: "[optional] [args...] description"
---
```

### Skill Activation State

Tracked in `.omx/state/skill-active-{session-id}.json`:

```json
{
  "sessionId": "...",
  "active": {
    "skill": "deep-interview",
    "depth": "standard",
    "startedAt": "2026-06-19T13:39:00Z",
    "phase": "ambiguity_scoring"
  }
}
```

### Keyword Detection

**File:** `src/hooks/keyword-detector.ts`

Codex's `UserPromptSubmit` hook detects keywords and auto-routes:
- `"deep interview"`, `"interview"`, `"don't assume"`, `"ouroboros"` → `$deep-interview`
- `"analyze"`, `"investigate"` → `$analyze` (read-only deep analysis)
- Natural language mappings in keyword registry

**Registry File:** `src/hooks/keyword-registry.ts` (comprehensive keyword list).

---

## 4. Hook System & codex-native-hook.ts

### Architecture

The `codex-native-hook.ts` is the **runtime engine** that:
1. Intercepts all Codex hook events
2. Reads/updates `.omx/state/` for skill activation, mode tracking, team state
3. Injects instructions or gates execution based on mode state
4. Returns JSON for Codex to use in the next prompt

### Key Responsibilities

#### SessionStart
- Initialize session state (`.omx/state/session-{id}.json`)
- Read prior mode state (ralph, ultragoal, team)
- Initialize skill activation state
- Build wiki context

#### UserPromptSubmit
- Detect skill keywords; record in skill-active state
- Detect mode keywords (autopilot, ralph, ultragoal, team)
- Inject AGENTS.md overlay if session-scoped
- Triage heuristic (detect and gate risky prompts)
- Reconcile HUD for prompt submission (if tmux-backed)

#### PreToolUse
- Detect MCP transport failures (Hermes/code-intel unavailable)
- Inject pre-tool guidance for known patterns
- Record tool call for team worker tracking

#### PostToolUse
- Handle team worker success notifications
- Auto-nudge leader if worker stalled
- Record tool result for session history

#### PreCompact
- Build wiki pre-compact context
- Snapshot session state

#### Stop
- Gate skill stops (e.g., prevent stopping `ralplan` mid-planning)
- Transition mode state (complete ultragoal step, archive ralph, etc.)
- Trigger ralph resume if applicable
- Return `outputJson` for final prompt injection

### State Files Written/Read

| State File | Location | Purpose |
|-----------|----------|---------|
| `session-{id}.json` | `.omx/state/` | Session log, transcript, metrics |
| `skill-active-{id}.json` | `.omx/state/` | Active skill, depth, phase |
| `ultragoal-{id}.json` | `.omx/ultragoal/` | Multi-goal ledger and checkpoints |
| `ralph-{id}.json` | `.omx/state/ralph/` | Ralph persistent loop state |
| `team-{name}/manifest.json` | `.omx/state/team/` | Team worker list and assignments |
| `team-{name}/worker-{id}.json` | `.omx/state/team/` | Worker task, completion, checkpoint |
| `triage-{id}.json` | `.omx/state/` | Triage decisions and suppressions |
| `autopilot-{id}.json` | `.omx/state/autopilot/` | Autopilot FSM phase |

### Input/Output Contract

**Input (from Codex hook):**
```json
{
  "eventName": "UserPromptSubmit",
  "payload": {
    "prompt": "user's message",
    "sessionId": "...",
    "turnNumber": 5,
    "priorMessages": [...],
    "toolResults": [...]
  }
}
```

**Output (to Codex):**
```json
{
  "hookEventName": "UserPromptSubmit",
  "omxEventName": "deep_interview_active",
  "skillState": {
    "skill": "deep-interview",
    "phase": "ambiguity_scoring",
    "round": 3
  },
  "outputJson": {
    "instruction": "Enforce this instruction before processing the prompt",
    "agentOverlay": { "model": "...", "instructions": "..." }
  }
}
```

---

## 5. MCP Integration

### OMX MCP Servers

OMX exposes durable runtime state via **Model Context Protocol (MCP)** servers for Codex to access.

| Server | Purpose | Provides | Located At |
|--------|---------|----------|-----------|
| `omx_state` | Mode state, skill activation, workflow ledgers | Read/write `.omx/state/*` files | `src/mcp/state-server.ts` |
| `omx_wiki` | Wiki knowledge base (markdown-first, search-first) | Wiki queries, list, refresh | `src/mcp/wiki-server.ts` |
| `omx_memory` | Durable memory (notes, observations, context snapshots) | Memory CRUD | `src/mcp/memory-server.ts` |
| `omx_code_intel` | Code intelligence queries (symbols, references, definitions) | Read-only codebase indexing | `src/mcp/code-intel-server.ts` |
| `omx_trace` | Trace operations and execution flow | Read-only execution traces | `src/mcp/trace-server.ts` |
| `omx_hermes` | Bridge to external system (OpenClaw notifications) | Send notifications to Discord/Slack/custom | `src/mcp/hermes-server.ts` |

### MCP Setup

**Plugin Mode:**
- Codex discovers MCP servers from plugin manifest (disabled by default)
- Enable with `omx setup --mcp compat`
- Servers run in sidecar processes spawned by Codex

**Legacy Mode:**
- Registered in `.codex/config.toml` under `[[mcp_servers]]`
- `command`: `omx mcp-serve <server-name>`

### state-server Interface

**Resources:**
- `state://mode/{session-id}/current` → current mode/skill state
- `state://ultragoal/{session-id}/ledger` → multi-goal checkpoint ledger
- `state://ralph/{session-id}` → ralph persistent state
- `state://team/{team-name}/manifest` → team worker manifest

**Tools:**
- `state_read(path: string)` → read state file
- `state_write(path: string, content: object)` → write state file
- `state_list(dir: string)` → list state directory

### wiki-server Interface

**Resources:**
- `wiki://search?query=...` → search wiki
- `wiki://page/{name}` → get specific page
- `wiki://list` → list all wiki pages

**Tools:**
- `wiki_query(query: string)` → search and rank results
- `wiki_list()` → enumerate all pages
- `wiki_refresh()` → rebuild wiki index
- `wiki_lint()` → validate wiki structure

---

## 6. Sidecar System

The **sidecar** is a **read-only visualization** of team/multi-agent state in real time.

### sidecar Command

```bash
omx sidecar [--watch] [--json] [--tmux]
```

**Options:**
- `--watch` — poll and update in real time
- `--json` — output raw JSON instead of formatted text
- `--tmux` — render inside a tmux pane (used by HUD)

### Sidecar Output

**JSON Format:**
```json
{
  "teamName": "feature/auth",
  "leader": {
    "paneId": "%0",
    "mode": "ultragoal",
    "currentTask": "implement auth endpoint",
    "taskDone": false
  },
  "workers": [
    {
      "workerId": "worker-1",
      "paneId": "%1",
      "task": "write tests",
      "status": "in_progress",
      "checkpoint": "test_harness_ready"
    }
  ],
  "meta": {
    "startedAt": "2026-06-19T13:39:00Z",
    "elapsed": "10m"
  }
}
```

---

## 7. AGENTS.md Template & Guidance Schema

### AGENTS.md Purpose

**AGENTS.md** is the **top-level operating contract** for a workspace or session. It defines:
- Autonomy directives (permissions, guardrails)
- Execution principles (work direct vs. delegate, verification rules)
- Mode selection (when to use `$deep-interview`, `$ralplan`, `$team`, etc.)
- Specialist routing (which roles to use for which tasks)
- Delegation rules (worker protocols, concurrency limits)
- Verification requirements

### Template Location

`templates/AGENTS.md` in OMX package.

### Key Sections

1. **Autonomy Directive** (lines 1–6)
   - Instructs the agent to execute without asking permission for obvious steps
   - Gates only on irreversible, destructive, or credential-gated actions

2. **Operating Principles** (lines 22–47)
   - Solve directly when safe; delegate only if it materially improves quality/speed
   - Keep progress short and concrete
   - Prefer evidence over assumption
   - Check official docs before unfamiliar SDKs

3. **Delegation Rules** (lines 56–71)
   - `$deep-interview` for unclear intent
   - `$ralplan` for plan review before execution
   - `$team` for coordinated parallel work
   - `$ralph` for persistent single-owner loops
   - Solo execution for already-scoped work

4. **Specialist Routing** (lines 91–101)
   - `explore` for repo-local lookup
   - `researcher` for official docs and external reference
   - `dependency-expert` for package/framework selection
   - Explicit mixed routing examples

5. **Skill Invocation** (lines 120–122)
   - `$name` invokes a skill
   - `/skills` browses installed skills

6. **Verification** (lines 140–150)
   - Define claim + success criteria
   - Run smallest validation that proves it
   - Read output; iterate if validation fails

7. **Execution Protocols** (lines 152–175)
   - Mode selection based on work type
   - Command routing (Codex tools vs. sparkshell)
   - Leader vs. worker responsibilities
   - Stop/escalate gates

### Runtime Marker Contracts

OMX overlays preserve these marker contracts to allow non-destructive updates:

```markdown
<!-- OMX:RUNTIME:START --> ... <!-- OMX:RUNTIME:END -->
<!-- OMX:TEAM:WORKER:START --> ... <!-- OMX:TEAM:WORKER:END -->
<!-- OMX:GUIDANCE:OPERATING:START --> ... <!-- OMX:GUIDANCE:OPERATING:END -->
<!-- OMX:GUIDANCE:SPECIALIST-ROUTING:START --> ... <!-- OMX:GUIDANCE:SPECIALIST-ROUTING:END -->
<!-- OMX:GUIDANCE:VERIFYSEQ:START --> ... <!-- OMX:GUIDANCE:VERIFYSEQ:END -->
```

When `omx setup --merge-agents` runs, it updates content between these markers without overwriting user guidance outside.

### Session-Scoped AGENTS.md

For active execution, a **session-scoped overlay** AGENTS.md is generated that:
- Inherits durable scope AGENTS.md (user or project)
- Injects runtime models, skills, and context for the current session
- Includes mode-specific team worker guidance if active
- Is removed at session end

---

## 8. Configuration Schema

### .codex/config.toml

OMX extends Codex's `config.toml` with:

```toml
[model]
model_name = "gpt-5.5"
model_context_window = 250000
model_auto_compact_token_limit = 200000
model_reasoning_effort = "medium"  # Set by --high, --xhigh, omx reasoning

[[mcp_servers]]
name = "omx_state"
command = "omx mcp-serve omx_state"

[[mcp_servers]]
name = "omx_wiki"
command = "omx mcp-serve omx_wiki"

[[mcp_servers]]
name = "omx_trace"
command = "omx mcp-serve omx_trace"

[[mcp_servers]]
name = "omx_code_intel"
command = "omx mcp-serve omx_code_intel"
```

### .omx-config.json (OMX-Specific)

Located in repo root or user home. Documented in `docs/reference/omx-config-schema-routing.md`.

```json
{
  "setup": {
    "scope": "project",
    "installMode": "plugin",
    "mcpMode": "compat"
  },
  "defaultModels": {
    "frontier": "claude-opus-4-8",
    "spark": "claude-opus-4-8"
  },
  "team": {
    "defaultWorkerCount": 3
  }
}
```

---

## 9. Integrations: Codex ↔ OMX ↔ maw

### OMX ↔ Codex

**Direction:** Bidirectional

**Codex → OMX:**
- Codex invokes OMX via native hooks (SessionStart, UserPromptSubmit, etc.)
- Codex reads MCP resources (state, wiki, memory)
- Codex calls MCP tools (state_read, wiki_query)

**OMX → Codex:**
- OMX CLI invokes `codex` subprocess for interactive/exec launch
- OMX injects AGENTS.md overlay for session
- OMX returns hook output JSON for Codex to apply

### OMX ↔ maw (maw Integration)

**Purpose:** maw is a **tmux orchestrator** for persistent team runtime.

**Current Status:** OMX **does not directly call maw**; instead OMX owns tmux pane management directly.

**Legacy maw Path:** Earlier OMX versions may have sent work to maw; current versions manage tmux directly via `src/team/tmux-session.ts`.

**Future Integration:** If/when maw becomes the durable team coordination layer, OMX would:
1. Delegate worktree creation to maw
2. Submit worker tasks to maw via CLI or IPC
3. Read worker state from maw's persistent ledger
4. Coordinate HUD/resize events through maw

### Codex Plugin Architecture

**Plugin Marketplace Discovery:**
- Codex CLI fetches plugin metadata from marketplace
- OMX plugin bundled at `plugins/oh-my-codex/`
- Marketplace metadata at `.agents/plugins/marketplace.json`

**Plugin → OMX CLI:**
- Codex plugin calls installed `omx` CLI (e.g., `omx mcp-serve omx_state`)
- OMX CLI owns the runtime; plugin is a metadata facade

**Scope Preference:**
- Plugin mode installs bundled skills, keeps persistent AGENTS.md
- Legacy mode copies skills/prompts to `~/.codex/` or `./.codex/`
- Project scope has higher precedence than user scope

---

## 10. Workflow Execution Paths

### Path 1: Solo Interactive Session

```
$ omx --worktree=feat/task --madmax --high
→ Spawn detached tmux with HUD
→ Launch Codex in main pane
→ SessionStart hook: initialize session state
→ User types prompt
→ UserPromptSubmit hook: detect skill, inject overlay
→ Codex executes; PostToolUse hooks track progress
→ User types $ralplan "review plan"
→ Hook detects ralplan skill; injects ralplan SKILL.md
→ Codex reviews and approves plan
→ User types $ultragoal "implement plan"
→ Hook detects ultragoal; checkpoint in .omx/ultragoal/
→ Codex executes goals incrementally
→ On Stop: hook archives ultragoal state
→ Session ends
```

### Path 2: Non-Interactive Exec with Overlay

```
$ omx exec "implement the feature"
→ No tmux; direct subprocess
→ SessionStart hook: init state
→ UserPromptSubmit hook: inject overlay (AGENTS.md, skills)
→ Codex processes prompt
→ No interactive Stop; auto-complete or timeout
→ Exit with code
```

### Path 3: Team Parallel Execution

```
$ omx team 3:executor "implement 3 features in parallel"
→ Spawn tmux window with HUD (main pane) + 3 worker panes
→ Write .omx/state/team/manifest.json with task assignments
→ Each worker: SessionStart hook → init worker state
→ Each worker: UserPromptSubmit → inject worker AGENTS.md overlay
→ Workers execute in parallel; PostToolUse → notify leader
→ Leader: reconcile worker progress; adjust HUD
→ On worker Stop: update worker checkpoint
→ On leader Stop: finalize team, write completion ledger
```

### Path 4: Ralph Persistent Loop

```
$ omx ralph "keep working on this until tests pass"
→ Write initial ralph-{id}.json in .omx/state/ralph/
→ Enter persistent loop in Codex
→ Before each Stop: hook checks ralph state
→ If not complete (tests not passing): resume automatically
→ SessionStart (resumed): read prior ralph state
→ Continue execution
→ On final Stop: persist completion status
```

---

## 11. Extension Points & Customization

### Hook-Driven Extensibility

**File:** `src/hooks/extensibility/`

OMX provides a hook event system for custom workflows:

1. **Register a hook:**
   ```javascript
   // In .omx/hooks/my-hook.mjs
   export function onPostToolUse(event) {
     // Custom logic
     return { instruction: "..." };
   }
   ```

2. **Dispatch from native-hook:**
   - `buildHookEvent()` in `src/hooks/extensibility/events.ts`
   - `dispatchHookEventRuntime()` in `src/hooks/extensibility/runtime.ts`

### Custom Skill Creation

**Create a skill:**
```bash
omx skill create "my-skill"
```

Generates:
- `.codex/skills/my-skill/SKILL.md` (or plugin location)
- Frontmatter with name, description, argument hints
- Workflow steps template

**Skill routing:**
- Auto-keyword detection (if name matches common patterns)
- Or explicit `$my-skill` invocation

### Persistent Adapter Foundations

**Adapt command:**
```bash
omx adapt scaffold <target-name>
```

Creates durable external adapter for:
- Custom notification gateways (OpenClaw)
- External logging systems
- Custom state backends

---

## 12. Deployment Model

### Installation Paths

#### Path A: Plugin (Recommended)

```bash
npm install -g oh-my-codex
omx setup --plugin  # or just omx setup (plugin is default)
```

- Codex marketplace discovery
- Plugin cached at `~/.codex/plugins/cache/oh-my-codex/`
- Persistent AGENTS.md at `~/.codex/AGENTS.md` or `./.AGENTS.md`
- Skills bundled in plugin

#### Path B: Legacy

```bash
npm install -g oh-my-codex
omx setup --legacy
```

- Skills copied to `~/.codex/skills/` or `./.codex/skills/`
- Prompts copied to `~/.codex/prompts/` or `./.codex/prompts/`
- Native hooks in `.codex/hooks.json` (shared with user hooks)

#### Path C: Combined (Codex CLI via npm)

```bash
npm install -g @openai/codex oh-my-codex
codex login
omx setup
```

### Preinstall Checks

```bash
omx doctor           # Check install health
codex --version      # Verify Codex CLI
codex login status   # Verify auth
omx exec --skip-git-repo-check -C . "OMX-EXEC-OK"  # Smoke test
```

---

## 13. Key Files & Architecture

### Source Organization

```
src/
├── cli/                         # CLI commands
│   ├── index.ts                 # Main command router
│   ├── setup.ts                 # omx setup logic
│   ├── team.ts                  # omx team
│   ├── ralph.ts                 # omx ralph
│   ├── ultragoal.ts             # omx ultragoal
│   ├── mcp-serve.ts             # omx mcp-serve
│   └── ...
├── scripts/
│   ├── codex-native-hook.ts     # Native hook entry point
│   ├── codex-native-pre-post.ts # Pre/Post tool guidance
│   └── notify-hook/             # Auto-nudge, team worker notifications
├── mcp/                         # MCP servers
│   ├── state-server.ts
│   ├── wiki-server.ts
│   ├── memory-server.ts
│   ├── code-intel-server.ts
│   └── ...
├── hooks/
│   ├── keyword-detector.ts      # Skill keyword detection
│   ├── keyword-registry.ts      # Complete keyword list
│   ├── agents-overlay.ts        # Session AGENTS.md injection
│   ├── session.ts               # Session state mgmt
│   └── extensibility/           # Custom hook system
├── state/                       # State management
│   ├── skill-active.ts
│   ├── workflow-transition.ts
│   └── ...
├── team/                        # Team/tmux coordination
│   ├── tmux-session.ts          # Tmux pane/window management
│   ├── state.ts                 # Team state (manifest, phase, attention)
│   ├── worktree.ts              # Worktree management
│   └── model-contract.ts        # Worker model selection
├── ultragoal/                   # Multi-goal execution
│   ├── artifacts.ts             # Ledger, checkpoints
│   └── ...
├── ralph/                       # Ralph persistent loop
│   ├── completion-audit.ts
│   └── ...
├── hud/                         # HUD statusline/visualization
│   ├── tmux.ts                  # Tmux HUD pane management
│   ├── state.ts                 # HUD state
│   └── reconcile.ts
├── config/                      # Config management
│   ├── generator.ts             # config.toml generation
│   ├── mcp-registry.ts          # MCP server registry
│   └── ...
├── autopilot/                   # Autopilot FSM
├── notifications/               # Discord/Slack/Telegram
├── adapt/                       # Adapter framework
├── types/                       # TypeScript types
└── utils/
    ├── paths.ts                 # Path resolution (.omx/, .codex/)
    ├── platform-command.ts      # Cross-platform command execution
    └── ...
```

### Key Exports

**From `src/cli/index.ts`:**
- `resolveSetupInstallModeArg()` — parse `--plugin`/`--legacy` flags
- `resolveSetupMcpModeArg()` — parse `--mcp compat` flags
- `readPersistedSetupPreferences()` — load setup choices from disk
- `resolveCodexHomeForLaunch()` — find active Codex home

**From `src/mcp/state-server.ts`:**
- `createStateServer()` — instantiate MCP state server
- `readModeState()` — load mode state file

**From `src/team/tmux-session.ts`:**
- `isTmuxAvailable()` — check tmux availability
- `listCurrentWindowPanes()` — enumerate tmux panes in window
- `resizeTmuxPane()` — resize pane to dimensions

---

## 14. Performance & Limits

### Team Concurrency

- **Max concurrent agents:** min(16, CPU cores - 2) per workflow
- **Max agents per workflow lifetime:** 1000
- **Max items in parallel()/pipeline():** 4096

### State File Sizing

- **Session state:** typically 10–500 KB depending on transcript depth
- **Ultragoal ledger:** typically 5–50 KB
- **Team manifest:** typically 2–10 KB per worker

### Hook Response Time

- **SessionStart:** < 100 ms
- **UserPromptSubmit:** < 200 ms (keyword detection + overlay injection)
- **PreToolUse:** < 50 ms
- **PostToolUse:** < 100 ms

### MCP Server Overhead

- Each MCP server is a separate process (~20 MB memory overhead)
- State server typically < 50 MB with full session history
- Wiki server grows with `.omx/wiki/` size

---

## 15. Security Considerations

### Sandbox & Approval Gates

- `--madmax` (`--dangerously-bypass-approvals-and-sandbox`) removes Codex approval gates
- Use **only in trusted repos** with careful code review
- Team workers run with inherited leader flags (can be constrained via `OMX_TEAM_WORKER_LAUNCH_ARGS`)

### Secret Redaction

- Auth tokens in `.omx/state/` are redacted in transcripts
- Codex redaction (src/auth/redact.ts) applied to all logged state
- MCP state server sanitizes payloads before exposing

### File Permissions

- `.omx/state/` files are user-readable only (0o600 when possible)
- `.codex/config.toml` can contain keys; treat as sensitive
- `.codex/` home directory permissions should be restricted

---

## 16. Troubleshooting & Diagnostics

### Check Install Health

```bash
omx doctor           # General installation check
omx doctor --team    # Team runtime check
omx list --json      # Installed skills + agents
```

### Check Codex Auth

```bash
codex login status
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"
```

### Debug Hook Execution

Set env var:
```bash
OMX_STATE_VERBOSE=1 omx [command]
```

Reads state files and logs transitions.

### Inspect State Files

```bash
omx state read --input '{"path":".omx/state/skill-active-*.json"}' --json
```

### Reset State

```bash
omx cleanup          # Remove stale state and orphaned MCP processes
rm -rf .omx/state/   # Full state reset (destructive)
```

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **OMX** | oh-my-codex; workflow orchestration layer for Codex CLI |
| **Skill** | Reusable workflow distributed as SKILL.md; invoked with `$name` |
| **Deep-Interview** | Socratic clarification skill; gates ambiguity scoring before execution |
| **Ralplan** | Review and consensus skill; approves architecture before execution |
| **Ultragoal** | Multi-goal execution mode; durable checkpoints in `.omx/ultragoal/` |
| **Ralph** | Persistent single-owner loop; auto-resumes on Stop until complete |
| **Team** | Parallel multi-worker execution; spawns tmux panes; workers report upward |
| **AGENTS.md** | Top-level operating contract; defines autonomy, delegation rules, verification |
| **Hook** | Codex lifecycle event (SessionStart, UserPromptSubmit, Stop, etc.) |
| **MCP** | Model Context Protocol; servers expose durable state to Codex |
| **Worktree** | Isolated git worktree for safe `-w/--worktree` launches |
| **HUD** | Heads-up display; tmux pane showing session/team/mode status |
| **Sidecar** | Read-only visualization of team state (real-time poll) |
| **Sparkshell** | Shell-native sidecar for bounded command execution/summarization |
| **Plugin** | Codex plugin discovery of OMX; bundled skills/hooks from cache |
| **Adapter** | Durable external bridge (OpenClaw gateway, notifications, etc.) |
| **Autopilot** | Fully autonomous execution mode (no human approval gates) |
| **Triage** | Heuristic safety check before execution (risky pattern detection) |

---

## 18. References

- **README:** https://github.com/Yeachan-Heo/oh-my-codex
- **Docs:** `docs/` directory in repo
- **AGENTS.md Schema:** `docs/guidance-schema.md`
- **Hook Mapping:** `docs/codex-native-hooks.md`
- **Plugin Integration:** `.agents/plugins/marketplace.json`
- **Release Notes:** `CHANGELOG.md`
- **Contributing:** `CONTRIBUTING.md`

---

**Document Generated:** 2026-06-19 13:39 UTC  
**OMX Version:** 0.18.13  
**Source:** oh-my-codex GitHub repository
