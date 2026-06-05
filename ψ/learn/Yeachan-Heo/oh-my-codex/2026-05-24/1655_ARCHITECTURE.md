# oh-my-codex Architecture Deep Dive

**Project**: oh-my-codex (OMX)  
**Repository**: https://github.com/Yeachan-Heo/oh-my-codex  
**Analyzed**: 2026-05-24  
**Codebase Size**: ~253K lines of TypeScript + 6 Rust crates  
**Package Version**: 0.18.2

---

## What is oh-my-codex?

**OMX is a multi-agent orchestration layer and workflow runtime for OpenAI Codex CLI.**

Not a replacement for Codex, but a working layer around it that adds:
- **30+ specialized agent prompts** as Codex CLI slash commands (`$deep-interview`, `$ralplan`, `$ultragoal`, etc.)
- **35+ workflow skills** (SKILL.md files bundled in npm package)
- **Durable state management** under `.omx/` directory (plans, logs, memory, team runtime state)
- **MCP servers** for state, wiki, trace, code intelligence
- **Team runtime** with tmux/psmux for coordinated multi-agent execution
- **CLI tool** (`omx`) for setup, diagnostics, team management
- **Native Codex hooks** for lifecycle integration

**Target use case**: Stronger Codex sessions with better workflows, persistent state, and multi-agent coordination.

---

## Directory Structure & Organization Philosophy

```
oh-my-codex/
├── src/                           # TypeScript source (~250K lines)
│   ├── index.ts                   # Package exports
│   ├── cli/                       # CLI entry points
│   │   ├── omx.ts                 # Shebang entry (dist/cli/omx.js from npm bin)
│   │   ├── index.ts               # Main CLI dispatcher (100+ commands)
│   │   ├── setup.ts               # Installation & bootstrap
│   │   ├── doctor.ts              # Diagnostics & validation
│   │   ├── team.ts                # Team runtime orchestration
│   │   ├── ralph.ts               # Ralph (persistent single-owner loop)
│   │   ├── ultragoal.ts           # Ultragoal (durable multi-goal ledger)
│   │   ├── explore.ts             # omx explore (read-only repo lookup)
│   │   └── sparkshell.ts          # Shell exec with caching & summarization
│   ├── runtime/                   # Execution state & lifecycle
│   │   ├── bridge.ts              # TypeScript wrapper over omx-runtime binary
│   │   ├── run-outcome.ts         # Command execution results
│   │   ├── run-state.ts           # Durable session state
│   │   ├── process-tree.ts        # Process hierarchy tracking
│   │   └── terminal-lifecycle.ts  # Terminal attachment/detach events
│   ├── team/                      # Multi-agent tmux coordination
│   │   ├── worker.ts              # Agent/worker process management
│   │   ├── state-root.ts          # Team state directory resolution
│   │   ├── runtime.ts             # Team execution engine
│   │   ├── cross-rebase.ts        # Worktree rebasing across workers
│   │   └── hardening.ts           # Verification gates for team execution
│   ├── mcp/                       # Model Context Protocol servers
│   │   ├── state-server.ts        # `.omx/state/` SSOT server
│   │   ├── trace-server.ts        # Execution trace & discovery
│   │   ├── wiki-server.ts         # Project knowledge repository
│   │   ├── code-intel-server.ts   # Repository code indexing
│   │   ├── hermes-server.ts       # Notifications & messaging
│   │   ├── hermes-bridge.ts       # OpenClaw notification gateway
│   │   └── state-paths.ts         # `.omx/` directory layout
│   ├── ralph/                     # Ralph workflow (persistent loop)
│   │   ├── persistence.ts         # Session-scoped state
│   │   ├── completion-audit.ts    # Ralph completion detection
│   │   └── ralph-phase.ts         # Phase tracking (initial, iterate, verify)
│   ├── ultragoal/                 # Ultragoal workflow (multi-goal ledger)
│   │   ├── checkpoint.ts          # Goal ledger checkpoints
│   │   ├── phases.ts              # Goal workflow phases
│   │   └── completion.ts          # Goal completion criteria
│   ├── planning/                  # $ralplan & research workflows
│   ├── autoresearch/              # $autoresearch & research gates
│   ├── goal-workflows/            # $deep-interview, $prometheus-strict
│   ├── verification/              # Verification & gating logic
│   ├── hooks/                     # Codex native hook handlers
│   ├── hud/                       # Terminal UI (dashboard & monitoring)
│   ├── session-history/           # Session replay & recovery
│   ├── catalog/                   # Agent/skill definitions & documentation
│   ├── config/                    # Config generation & merging
│   ├── agents/                    # Agent prompt definitions
│   ├── types/                     # TypeScript type definitions
│   ├── utils/                     # Shared utilities
│   └── scripts/                   # Build & development scripts
├── crates/                        # Rust binaries & libraries
│   ├── omx-runtime/               # Rust runtime executor (dispatcher binary)
│   ├── omx-runtime-core/          # Core runtime state machine
│   ├── omx-mux/                   # Tmux adapter & messaging
│   ├── omx-sparkshell/            # Shell execution + redaction + caching
│   ├── omx-api/                   # HTTP API bridge
│   └── omx-explore/               # Repository search harness
├── skills/                        # 35+ workflow SKILL.md files
│   ├── deep-interview/
│   ├── ralplan/
│   ├── prometheus-strict/
│   ├── ultragoal/
│   ├── ralph/
│   ├── team/
│   └── ... 29 more
├── prompts/                       # Agent prompt templates
├── plugins/                       # Codex plugin mirror (marketplace sync)
├── missions/                      # Community contribution workflows
├── playground/                    # ML/optimization demos
├── docs/                          # Architecture, recipes, references
└── templates/                     # Model instruction templates
```

---

## Core Abstractions & Their Relationships

### 1. **The Execution Stack (TS + Rust)**

```
┌─────────────────────────────────────────────────────┐
│  CLI Layer (TypeScript)                             │
│  omx setup | omx team | omx exec | omx doctor       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Runtime Bridge (TypeScript)                        │
│  Thin wrapper: calls omx-runtime binary             │
│  Reads Rust-authored JSON compatibility views       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Rust Runtime (omx-runtime binary)                  │
│  - Parses RuntimeCommand (JSON)                     │
│  - Executes state mutations (authority, dispatch)   │
│  - Persists state to `.omx/`                        │
│  - Emits RuntimeEvent (JSON)                        │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Runtime Core (Rust library)                        │
│  - Authority lease system (ownership & concurrency) │
│  - DispatchLog (deliver tasks to tmux)              │
│  - MailboxLog (worker-to-worker messaging)          │
│  - ReplayState (crash recovery)                     │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Mux Adapter (omx-mux + omx-runtime)                │
│  - Tmux session/pane target resolution              │
│  - send_keys, capture-pane commands                 │
│  - Delivery confirmation & readiness                │
└─────────────────────────────────────────────────────┘
```

### 2. **Runtime State Machine (Rust Core)**

**Authority System** (mutual exclusion for multi-agent safety):
- Leader acquires & renews authority lease with owner + lease_id + expiry
- Followers cannot execute dispatch while leader holds lease
- Lease stale detection (120s timeout = STALE_HEARTBEAT_MS)
- Used by team runtime to ensure only one worker has authority at a time

**Dispatch System** (task delivery to Codex/tmux):
- Queue → Notify → Deliver → (optional) Confirmed
- DispatchRecord: request_id, target, status, metadata, timestamps
- Delivery confirmation: narrow/wide capture, verify_delay, retry policy
- Used to send prompts/goals to active Codex sessions

**Mailbox System** (inter-worker messaging):
- From/to worker IDs, message body, delivery tracking
- Worker-to-worker notifications without tmux coupling

**Replay System** (crash recovery):
- Cursor points to last processed event
- Pending events re-executed on recovery
- Used by team runtime to resume after crash

### 3. **Tmux Adapter (omx-mux Rust crate)**

Core abstractions:
- **MuxOperation**: resolve-target, send-input, capture-tail, inspect-liveness, attach, detach
- **MuxTarget**: DeliveryHandle (session:window.pane), Detached
- **InputEnvelope**: normalized text + submit policy (# presses, delay_ms)
- **SubmitPolicy**: enter(presses, delay_ms) — how many times to press Enter
- **ConfirmationPolicy**: narrow_capture_lines, verify_delay_ms, verify_rounds, etc.
- **PaneReadinessReason**: Ok, Missing, ShellNotInjectable, etc.

Serialized as JSON for omx-runtime to consume.

### 4. **Shell Execution (omx-sparkshell Rust binary)**

Sparkshell handles:
- **Command execution** (fork+exec with stdio capture)
- **Tmux pane capture** (tmux capture-pane with tail-lines)
- **Shell script parsing** (resolve to argv)
- **Redaction** (strip secrets before returning)
- **Output summarization** (via Codex API if budget > threshold)
- **Caching** (hash-based dedup with TTL)
- **Line counting** (visible vs stderr tracking)

Returns JSON with stdout_lines, stderr_lines, body, evidence metadata.

### 5. **MCP Servers (TypeScript)**

State Server (`omx mcp-serve state`):
- SSOT for `.omx/state/` directory
- Exposes tools: read_state, write_state, list_sessions, etc.
- Used by Codex agents to query/update session state

Trace Server (`omx mcp-serve trace`):
- Execution trace discovery (find related files, commits, issues)
- Supports keyword + semantic search
- Used for repository lookup

Wiki Server (`omx mcp-serve wiki`):
- Project knowledge base (markdown under `omx_wiki/`)
- List, query, lint, refresh operations

Code Intel Server:
- Repository code indexing (functions, classes, imports)
- Symbol lookup for agents

Hermes Server:
- Notifications & messaging
- OpenClaw integration for external notifications

### 6. **Team Runtime (TypeScript + Rust)**

Team state:
- `.omx/team/<team-name>/` directory with worker assignments
- Workers: executor, verifier, designer roles
- Worktree per worker for isolation
- Cross-rebase: rebase worker branches onto common ancestor

Execution flow:
1. Leader acquires authority via omx-runtime
2. Leader spawns tmux panes for each worker
3. Each worker gets a RuntimeEngine snapshot for isolation
4. Workers execute concurrently in tmux
5. Leader polls for completion, rebases results, closes worktrees
6. Fallback to sequential if concurrent fails (cross-rebase smoke test)

---

## Entry Points (All of Them)

### **CLI**

**Global** (installed as `npm bin` via package.json):
```json
{
  "bin": { "omx": "dist/cli/omx.js" }
}
```

**Entry point hierarchy**:
1. `omx.ts` (shebang) → checks `dist/cli/index.js` exists → imports & calls `main(argv)`
2. `index.ts` (compiled to dist/cli/index.js) → dispatcher for 100+ subcommands
3. Subcommands dispatch to dedicated files (setup.ts, doctor.ts, team.ts, ralph.ts, etc.)

**Main commands** (from index.ts):
- `omx setup` → bootstrap OMX in project
- `omx doctor` → validate install
- `omx exec --skip-git-repo-check -C . "<prompt>"` → one-off execution
- `omx team 3:executor "<task>"` → spawn team
- `omx team status <team-name>`
- `omx ralph` → persistent single-owner loop
- `omx ultragoal` → multi-goal ledger
- `omx explore --prompt "..."` → read-only repo lookup
- `omx sparkshell git status` → shell with caching
- `omx wiki list | query | lint`
- `omx hud --watch` → monitoring dashboard
- `omx cancel` → cleanup dead processes

### **Rust Binaries**

**omx-runtime** (built by npm run build:explore:release):
- Entry: crates/omx-runtime/src/main.rs
- CLI: `omx-runtime schema | snapshot | mux-contract | exec <json>`
- Executes RuntimeCommand, emits RuntimeEvent, persists state

**omx-sparkshell** (built by npm run build:sparkshell):
- Entry: crates/omx-sparkshell/src/main.rs
- Usage: sparkshell runs shell commands with redaction, caching, summarization
- Returns JSON: stdout_lines, stderr_lines, body, evidence

**omx-api** (built by npm run build:api):
- HTTP API server (port 3000 by default)
- Used for dashboard communication

**omx-explore-harness** (built by npm run build:explore:release):
- Native Rust binary for fast repository search
- Used by `omx explore` CLI

### **MCP Servers**

Spawned by `omx mcp-serve <type>`:
```bash
omx mcp-serve state           # state-server.ts
omx mcp-serve trace           # trace-server.ts
omx mcp-serve wiki            # wiki-server.ts
omx mcp-serve code-intel      # code-intel-server.ts
omx mcp-serve hermes          # hermes-server.ts
```

Each listens on stdio for MCP Protocol messages.

### **Native Codex Hooks**

Registered in `.codex/hooks.json` (legacy) or `plugins/oh-my-codex/hooks/` (plugin):
- On session start: lifecycle bootstrap
- On prompt execution: inject OMX context
- On completion: update state, trigger notifications

---

## Core Dependencies

### **TypeScript Dependencies** (package.json)

```
@iarna/toml         - TOML config parsing
@modelcontextprotocol/sdk - MCP server implementation
zod@4.3.6           - Runtime schema validation
```

### **Rust Dependencies**

**omx-runtime-core**:
```toml
fs2 = "0.4"          - Filesystem locks (authority lease persistence)
serde = "1"          - Serialization
serde_json = "1"     - JSON codec
```

**omx-mux**:
```toml
serde = "1"
serde_json = "1"     - MuxOperation/MuxOutcome JSON contracts
```

**omx-sparkshell**:
```toml
omx-mux              - Uses build_capture_pane_args
```

**omx-runtime**:
```toml
omx-mux
omx-runtime-core     - RuntimeEngine, RuntimeCommand, RuntimeEvent
serde_json = "1"
```

**omx-api, omx-explore**: Minimal dependencies (libc for omx-explore)

### **Build System**

- **TypeScript** → JavaScript (tsc)
- **Rust** → Native binaries (cargo, profile.dist with LTO=thin)
- **npm run build** → TypeScript → dist/
- **npm run build:full** → TypeScript + all Rust binaries
- **npm run test** → Node.js test runner (node --test), includes Rust tests

---

## How Rust & TypeScript Relate

### **Design Pattern: Thin TS Wrapper, Heavy Rust Core**

**TypeScript** = orchestration, CLI, MCP servers, workflow logic, UI  
**Rust** = stateful runtime engine, tmux adapter, shell execution, performance-critical paths

**Interaction model**:

1. **CLI (TS)** → invokes Rust binary (`omx-runtime exec <json>`)
2. **omx-runtime (Rust)** → executes state mutation → writes JSON snapshot → stdout event
3. **Bridge (TS)** → parses JSON → uses for further orchestration

Example: `omx team <role> <task>`
```
team.ts (TS)
  ├─ Parse arguments
  ├─ Spawn tmux panes
  ├─ Call omx-runtime with QueueDispatch command (JSON)
  ├─ Wait for RuntimeEvent
  ├─ Monitor pane readiness via MuxAdapter
  ├─ Call omx-runtime with MarkDelivered (JSON)
  └─ Manage worktrees & cleanup
```

**Why split?**
- Rust is fast for state mutations, persistence, tmux operations
- TS is flexible for orchestration, MCP servers, workflow decisions
- JSON contract decouples them — can evolve independently
- Rust side versioned (RUNTIME_SCHEMA_VERSION) for compatibility

---

## Key Design Decisions

1. **Nothing is Deleted** — state versioning & recovery logs in `.omx/`
2. **Authority Lease** — mutex for concurrent multi-agent execution
3. **Sparkshell Caching** — dedup expensive shell calls (hashed + TTL)
4. **Tmux Adapter Pattern** — abstract target resolution + send/capture
5. **MCP Servers** — standard integration with Codex agents
6. **Worktree per Worker** — isolation + parallel execution in team mode
7. **Plugin Mirror** — keep Codex plugin in sync with npm package
8. **Signature Hooks** — native Codex lifecycle integration (not just commands)

---

## File Count & Scale

```
253,575 total TypeScript lines
6 Rust crates with 100-500 lines each
35 skill directories (workflow definitions)
30+ agent prompts (bundled in npm)
100+ CLI commands (dispatcher in index.ts)
8+ MCP servers
```

---

## Summary: What This Is

**oh-my-codex** is an opinionated, production-grade workflow orchestration layer for OpenAI Codex CLI. It trades simplicity (plain Codex) for durability (persistent state, multi-agent coordination, recovery). Core innovation is the Rust runtime engine + TypeScript orchestration split, with JSON contracts as the API boundary. Designed to grow from single-agent workflows (setup + $deep-interview + $ralplan + $ultragoal) to coordinated team execution (tmux + worktrees + authority leases).

Target user: Codex power users who want their Codex sessions to be durable, recoverable, and team-capable.
