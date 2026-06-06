# oh-my-codex (OMX) Architecture

**Version**: 0.18.9  
**Project**: Multi-agent orchestration layer for OpenAI Codex CLI  
**Language**: Rust (runtime) + TypeScript (CLI/runtime layer)  
**Node.js**: 20+  
**License**: MIT

---

## Overview

**oh-my-codex** is a workflow orchestration framework that augments the Codex CLI with:
- Better default workflows (`$deep-interview` → `$ralplan` → `$ultragoal`)
- Multi-agent team coordination with tmux-based execution
- Durable state management under `.omx/`
- Plugin system for extensibility
- Auth rotation and token management
- MCP (Model Context Protocol) integration as optional compatibility layer
- CLI-first control plane with JSON automation surfaces

The project is **not** a replacement for Codex—it is a workflow layer around it.

---

## Crate Architecture (Rust)

### Workspace Structure

Located in `crates/` with shared workspace metadata in root `Cargo.toml` (v0.18.9).

#### 1. **omx-mux** — Tmux abstraction layer

**Purpose**: Type-safe tmux operations and delivery contracts.

**Key exports**:
- `TmuxAdapter` — executes tmux operations (send-input, capture-tail, etc.)
- `MuxOperation` enum — serializable tmux commands
- `MuxTarget` — pane/session addressing
- `InputEnvelope` — normalized text + submit policy
- `SubmitPolicy` — defines how many Enter key presses and delay
- `ConfirmationPolicy` — verification strategies

**Contract**: 
```rust
pub const MUX_OPERATION_NAMES: &[&str] = &[
    "resolve-target",
    "send-input",
    "capture-tail",
    "inspect-liveness",
    "attach",
    "detach",
];
```

All operations are `serde_json` roundtrip-safe.

---

#### 2. **omx-runtime-core** — State machine for dispatch/authority

**Purpose**: Durable, replayed runtime state using file-based authority leasing and event replay.

**Key modules**:
- `authority.rs` — Lease acquisition/renewal for exclusive execution rights
- `dispatch.rs` — Command queue with transitions: pending → notified → delivered/failed
- `mailbox.rs` — Inter-worker message passing
- `engine.rs` — `RuntimeEngine` processes commands, produces events, persists state
- `replay.rs` — Replay handler for recovery from crashes

**State machine**:
```
Command:  AcquireAuthority | RenewAuthority | QueueDispatch | MarkNotified | MarkDelivered | MarkFailed | CreateMailboxMessage | ...
      ↓
RuntimeEngine.process()
      ↓
Event: AuthorityAcquired | DispatchQueued | DispatchNotified | DispatchDelivered | ...
```

**Persistence**: JSON files on disk at state-dir (loaded/saved with `fs2` for locking).

**Key invariant**: Authority is a lease. Commands fail if the owner cannot renew before `leased_until`.

---

#### 3. **omx-runtime** — Binary entry point for runtime operations

**Purpose**: CLI interface to `omx-runtime-core` and `omx-mux`.

**Command patterns**:
```bash
omx-runtime schema [--json]
omx-runtime snapshot [--state-dir=<dir>] [--json]
omx-runtime mux-contract
omx-runtime exec <json-command> [--state-dir=<dir>] [--compact]
```

**Examples**:
- `exec '{"command":"AcquireAuthority","owner":"leader","lease_id":"abc123","leased_until":"2026-06-06T10:00:00Z"}'`
- `exec '{"command":"QueueDispatch","request_id":"req-1","target":"worker-1"}'`

All input/output is JSON. State is persisted only if `--state-dir` is provided.

---

#### 4. **omx-sparkshell** — Bounded bounded inspection helper

**Purpose**: Fast, cost-optimized repository scanning (fallback model support).

**Key files**:
- `exec.rs` — Command execution
- `codex_bridge.rs` — Bridges to Codex subprocess
- `redaction.rs` — Redacts secrets from output
- `prompt.rs` — Summary instructions

Used by `omx explore --prompt "..."` for read-only repo lookups.

---

#### 5. **omx-api** — API schema and binary

**Purpose**: Exposes durable API for external consumers (rarely used directly).

**Exports**: JSON schema definitions for bridge contracts.

---

#### 6. **omx-explore** (not directly present in workspace)

**Purpose**: Full-featured codebase explorer (compiled separately).

---

## TypeScript/Node.js Layer

### Directory Structure

```
src/
├── cli/
│   ├── omx.ts                 # Entry point (ES module shim)
│   ├── index.ts               # Main CLI dispatcher
│   ├── team.ts                # Team lifecycle commands
│   ├── hooks.ts               # Hook registration
│   ├── tmux-hook.ts           # Tmux runtime hook
│   └── plugin-marketplace.ts  # Codex plugin registry
├── team/
│   ├── orchestrator.ts        # Phase state machine (team-plan → team-prd → team-exec → ...)
│   ├── state.ts               # Persistent team state (config, workers, tasks)
│   ├── state/
│   │   ├── tasks.ts           # Task claim + readiness logic
│   │   ├── mailbox.ts         # Inter-worker messaging
│   │   ├── dispatch.ts        # Dispatch request queue
│   │   └── locks.ts           # File-based locking primitives
│   ├── coordination-protocol.ts # Plan sharing between workers
│   ├── worker-bootstrap.ts    # Spawn worker with context
│   └── worktree.ts            # Git worktree management
├── state/
│   ├── operations.ts          # State mutation entry points
│   ├── skill-active.ts        # Active workflow tracking
│   ├── workflow-transition.ts # Approval/denylist for mode combinations
│   ├── mode-state-context.ts  # Mode-specific state access
│   └── paths.ts               # .omx/ directory layout
├── autopilot/
│   ├── fsm.ts                 # Phase enumeration: deep-interview → ralplan → ultragoal → ...
│   ├── deep-interview-gate.ts # Validate transition to ralplan
│   └── ralplan-gate.ts        # Validate transition to ultragoal
├── auth/
│   ├── index.ts               # Auth slot management
│   ├── rotation.ts            # Round-robin/priority slot rotation
│   ├── hotswap.ts             # Token swap during execution
│   ├── quota-detector.ts      # Rate-limit detection
│   └── storage.ts             # Persistent auth slot records
├── runtime/
│   ├── auth.ts                # Codex auth interaction
│   ├── bridge.ts              # Rust omx-runtime binary wrapper
│   ├── run-outcome.ts         # Execution result classification
│   └── session.ts             # Session state reading
├── hud/
│   ├── state.ts               # HUD rendering context builder
│   ├── authority.ts           # Authority lease display
│   └── types.ts               # Type definitions for HUD
├── sidecar/
│   ├── collector.ts           # Gather team state snapshot
│   ├── render.ts              # Format as TUI
│   ├── tmux.ts                # Sidecar pane management
│   └── types.ts               # Sidecar data structures
├── mcp/
│   ├── state-server.ts        # MCP server for state mutations
│   ├── state-paths.ts         # Session/scope resolution
│   └── trace-server.ts        # Event tracing MCP
├── hooks/
│   ├── keyword-detector.ts    # Parse $skill keywords
│   ├── agents-overlay.ts      # AGENTS.md injection
│   ├── triage-heuristic.ts    # Task complexity estimation
│   ├── codebase-map.ts        # Fast codebase snapshot
│   └── extensibility/
│       └── plugin-runner.ts   # Load hook plugins
├── ralph/
│   ├── contract.ts            # Phase definitions
│   ├── persistence.ts         # Durable ledger
│   └── completion-audit.ts    # Verify completion
├── ultra goalsgoal/
│   ├── context.ts             # Goal ledger context
│   └── (other structures)
└── notifications/
    ├── notifier.ts            # Dispatch notifications
    ├── hook-config.ts         # Notification routing
    └── lifecycle-dedupe.ts    # Suppress duplicate alerts
```

### Core Abstractions

#### 1. **CLI Entry Point** (`src/cli/omx.ts` → `dist/cli/index.js`)

ES module wrapper that imports the compiled TypeScript main.

**Flow**:
```
omx --worktree=feat/task --madmax --high
  ↓
parse args → resolve launch policy (direct/tmux/detached-tmux)
  ↓
create worktree if needed
  ↓
launch Codex CLI with setup
```

**Key flags**:
- `--worktree=<name>` — Git worktree for isolation
- `--madmax` — Bypass approval/sandbox (use in trusted repos)
- `--high` — Set `model_reasoning_effort="high"`
- `--direct` — No HUD/tmux, plain CLI
- `--tmux / --detached-tmux` — HUD management modes

---

#### 2. **State Machine: Autopilot FSM** (`src/autopilot/fsm.ts`)

Tracks workflow progression through approved phases.

**Phases** (in order):
1. `deep-interview` — Clarify scope
2. `ralplan` — Approve architecture
3. `ultragoal` — Durable multi-goal execution
4. `team` — Coordinated parallel execution
5. `ralph` — Persistent completion loop
6. `code-review` — Verification
7. `ultraqa` — Testing

**Terminal phases**: `waiting-for-user`, `complete`, `failed`

**Validation**:
- `deriveAutopilotChildPhase(state)` — Read current phase
- `normalizeAutopilotPhase(value)` — Parse phase from user input
- `isNextAutopilotPhase(current, next)` — Enforce ordering

---

#### 3. **Runtime Bridge** (`src/runtime/bridge.ts`)

**Purpose**: Thin wrapper over `omx-runtime` binary (Rust) for durable state.

**Types match Rust**:
- `RuntimeSnapshot` — read authority, dispatch backlog, replay state
- `RuntimeCommand` — JSON mutations (AcquireAuthority, QueueDispatch, MarkDelivered, etc.)
- `RuntimeEvent` — outcomes (AuthorityAcquired, DispatchQueued, etc.)
- `DispatchRecord`, `MailboxRecord` — JSON-serializable state

**Bridge contract**: All writes go through `execCommand(command, stateDir)` → spawns `omx-runtime exec` → reads JSON output.

**Fallback**: Set `OMX_RUNTIME_BRIDGE=0` to skip Rust bridge (uses TS-direct fallback).

---

#### 4. **Team Orchestration** (`src/team/`)

Implements multi-agent coordination using file-based state and tmux.

**State machine** (`src/team/orchestrator.ts`):
```
team-plan
   ↓ (PRD approved)
team-prd
   ↓ (execution plan ready)
team-exec
   ↓ (all work done)
team-verify
   ↓ (bugs found? retry)
team-fix ← → team-exec
   ↓ (no fix retries left)
failed / complete
```

**Key types** (`src/team/state.ts`):
- `TeamConfig` — name, worker_count, tmux_session, lifecycle_profile
- `WorkerInfo` — name, index, role, assigned_tasks, pane_id, worktree
- `TeamTask` — id, description, status (pending/claimed/in_progress/done), owner (worker)

**Operations**:
- `claimTask(task_id, worker_name)` — Acquire task with timeout
- `transitionTaskStatus(task_id, new_status)` — Update task state
- `sendDirectMessage(to_worker, body)` — Worker-to-worker message
- `broadcastMessage(body)` — All workers

**Locking**: File-based locks in `.omx/team/<team-name>/state/locks/`.

---

#### 5. **State Paths & Scoping** (`src/mcp/state-paths.ts`, `src/state/`)

**State root**: `.omx/state/{scope}/`

**Scopes** (resolved from session + mode):
- Standalone session: `.omx/state/session-{id}/`
- Team session: `.omx/state/team-{team-name}/`

**Per-scope files**:
- `autopilot-state.json` — Autopilot phase + questions
- `ralph-state.json` — Persistent completion ledger
- `ultragoal-state.json` — Multi-goal plan + status
- `skill-active-state.json` — **Canonical active workflow set**
- `{mode}-state.json` — Any other mode-specific data

**Key invariant**: `skill-active-state.json` is authoritative for which workflows are active. Prevents invalid combinations (e.g., `autopilot` + `team` simultaneously) using transition rules.

---

#### 6. **Auth Rotation** (`src/auth/`)

Manages multiple API keys / credential slots for quota avoidance.

**Strategy**:
- `AuthSlotRecord` — Persisted credential metadata
- `buildRotationPlan(slots, config)` — Order slots by mode (manual/round-robin/priority)
- `nextSlotAfter(order, current, exhausted)` — Pick next slot

**Config modes**:
- `"manual"` — Use specified slot only
- `"round-robin"` — Cycle through all slots
- `"priority"` — Use priority list, then others

**Integration**: Hooked into Codex subprocess launch to swap `OPENAI_API_KEY` or `CODEX_API_KEY` before each invocation.

---

#### 7. **Plugin System** (`src/hooks/extensibility/`)

Allows users to extend OMX with custom lifecycle hooks.

**Plugin loader** (`plugin-runner.ts`):
1. Load user hook plugin from file (ES module)
2. Create SDK context (`cwd`, `event`, `sideEffectsEnabled`)
3. Call `plugin.onHookEvent(event, sdk)`
4. JSON output with result (ok/error)

**Hook plugin interface**:
```typescript
export async function onHookEvent(event: HookEventEnvelope, sdk: HookPluginSdk) {
  // Consume event, optionally mutate .omx/ state
}
```

**Events**:
- Codex native hooks (in `plugins/oh-my-codex/hooks/hooks.json`)
- OMX plugin hooks (in `.omx/hooks/*.mjs`)
- Fallback: notify-hook, tmux-hook watchers

---

#### 8. **HUD (Heads-Up Display)** (`src/hud/`)

Real-time rendering of runtime state for tmux panes.

**Context** (`HudRenderContext`):
- `version`, `cwd`, `gitDisplay`
- `session` state (phase, active workflows)
- `team` state (phase, worker count, task summary)
- `ralph` state (completion percentage)
- `ultragoal` state (active goals, progress)
- `metrics` (timestamp, uptime, notification count)

**Presets**:
- `minimal` — One-line status
- `focused` — Current phase + key metrics
- `full` — All state + worker/task details

**Updates**: Polled from `.omx/state/` files on refresh interval (default 1s).

---

#### 9. **Sidecar** (`src/sidecar/`)

Optional right-side tmux pane for team monitoring.

**Flow**:
```
omx sidecar <team-name> --tmux
  ↓
collectSidecarSnapshot() → read team state + tasks
  ↓
renderSidecar() → format TUI
  ↓
launchSidecarTmuxPane() → create pane, run watch loop
```

**Output**: Worker list with task assignments, team phase, progress bars.

---

### Data Flow: CLI Command → Execution

#### Example: `$ultragoal "build the auth handler"`

**Path 1: Direct Codex execution**

```
User types: $ultragoal "build the auth handler"
  ↓
Codex CLI receives keyword ($ultragoal)
  ↓
keyword-detector.ts (hook) parses skill + intent
  ↓
Invokes ultragoal skill via $skill entry point
  ↓
Skill runs Codex with updated context + durable goals
  ↓
Agent works on goal sequentially
  ↓
goal-workflows updates .omx/ultragoal/ ledger on completion
  ↓
HUD displays goal status (in_progress → done → next)
```

**Path 2: Team execution**

```
User types: $team "split auth + payments across 2 workers"
  ↓
team.ts CLI dispatcher:
  1. create tmux session "omx-team-{name}"
  2. spawn worker-1, worker-2 with dedicated worktrees
  3. load TeamConfig + initialize task queue
  ↓
leader (main process) transitions phases: team-plan → team-prd → team-exec
  ↓
workers call `omx team api claim-task --json` to grab work
  ↓
For each worker:
  - Spawn Codex subprocess with worker context
  - Execute assigned task
  - Mark task complete in runtime state
  ↓
team-verify phase: check test coverage, errors
  ↓
If all pass: team-complete
   Else: team-fix (re-exec failing tasks, up to max_fix_attempts)
  ↓
Sidecar pane displays: worker statuses, task queue, phase progress
```

**Path 3: Ralph (single-owner persistent loop)**

```
User types: $ralph "debug the failing test"
  ↓
ralph.ts spawns persistent Codex loop:
  1. Attempt work
  2. Read test output
  3. If failed: ask user "should I retry?"
  4. Repeat until success or user stops
  ↓
ralph-state.json ledger records each turn (attempt #, outcome)
  ↓
ralph-persistence.ts verifies durable ledger on resume
```

---

### State Mutation & Authority

**All durable state writes** go through one of:

1. **TS-direct**: `src/state/operations.ts` (legacy/fallback)
   ```typescript
   await writeStateFile(path, data);
   ```

2. **Rust bridge** (preferred): `src/runtime/bridge.ts`
   ```typescript
   const event = await bridge.execCommand(
     { command: 'QueueDispatch', request_id: 'req-1', target: 'worker-1' },
     stateDir
   );
   ```

3. **MCP**: `src/mcp/state-server.ts` (compatibility layer)
   ```typescript
   omx_state.state_write({ mode: 'team', data: {...} })
   ```

**Authority lease cycle**:
```
Leader acquires lease (AcquireAuthority)
  ↓ (periodic Codex executions)
Leader renews lease before expiry (RenewAuthority)
  ↓ (worker reads dispatch queue)
Worker processes DispatchQueued items
  ↓
Worker marks DispatchDelivered
  ↓
Leader verifies completion and transitions phase
```

If leader crashes, another can acquire the lease after `leased_until` expires.

---

### Hook Lifecycle

**Codex native hooks** (plugin setup):

```
Codex subprocess starts
  ↓
plugin_hooks trigger (in `.codex/config.toml`)
  ↓
hook dispatcher (`.omx/hooks/*.mjs` or fallback)
  ↓
OMX injections:
  - keyword-detector: parse $skill / $deep-interview / $ralplan keywords
  - agents-overlay: inject AGENTS.md scoped guidance
  - triage-heuristic: estimate task size / complexity
  - codebase-map: fast static repo snapshot
  - explore-routing: $omx-explore → sparkshell fallback
  ↓
Codex prompt includes injected context
```

**Timeline**:
- Setup time: `omx setup` wires native hooks into `.codex/hooks.json` or plugin hooks registry
- Runtime: hooks run before every Codex model call
- Teardown: `omx uninstall` removes OMX hook entries

---

## Key Design Patterns

### 1. **File-Based State, JSON-Serialized**

All runtime state lives in `.omx/state/`, persisted as JSON files locked with `fs2`. No databases. Enables:
- Easy inspection/debugging (`cat .omx/state/session-xxx/ultragoal-state.json`)
- Crash recovery (replay from journal)
- Concurrent reads (multiple Codex workers read `.omx/` in parallel)

### 2. **Event Sourcing for Authority/Dispatch**

Rust runtime (`omx-runtime-core`) uses event-sourced dispatch log:
- Immutable event journal
- Replay from cursor for recovery
- Authority lease prevents concurrent mutation

### 3. **Tmux as Execution Fabric**

`omx-mux` abstracts tmux operations into type-safe enum. Enables:
- Durable output capture via `capture-pane`
- Input delivery with retry/confirmation
- Multi-pane HUD overlays
- Worker isolation (each gets a pane)

### 4. **CLI-First Control Plane**

- OMX is the control plane (sets up state, routes commands)
- Codex is the agent (executes, reads context from files)
- JSON CLI surfaces for automation
- MCP as optional compat layer (not required for runtime control)

### 5. **Auth Slots for Quota Management**

Multiple credential slots allow round-robin or priority-based rotation to avoid hitting rate limits. Useful for:
- Long-running multi-goal executions
- Team mode (many parallel workers)
- Fallback when one key exhausted

### 6. **Phase-Ordered Workflows**

Autopilot FSM enforces:
- Can't skip phases (must go deep-interview → ralplan → ultragoal)
- Can't go backward (except team-fix loop)
- Transition gates validate readiness (e.g., ralplan gate checks if plan approved)

---

## Dependencies

### Rust Workspace

- **serde / serde_json** — Serialization
- **fs2** — File locking
- **clap** (optionally, not visible in provided Cargo.toml) — CLI parsing

### Node.js Packages

- **@iarna/toml** — Parse TOML (for Codex `config.toml`)
- **@modelcontextprotocol/sdk** — MCP server implementation
- **zod** — Schema validation

**Dev**:
- **TypeScript**, **Biome**, **c8** — TS compilation, linting, coverage

---

## Build & Distribution

**Build steps**:
```bash
npm run build                # Compile TS → dist/
npm run build:sparkshell     # Build omx-sparkshell binary
npm run build:api            # Build API schema
npm run build:full           # All of above + explore harness
```

**Distribution**:
- Published to npm as `oh-my-codex` package
- Global install: `npm install -g oh-my-codex`
- Also shipped as Codex plugin under `plugins/oh-my-codex/` (marketplace)
- Native binaries (sparkshell, explore) bundled in npm tarball under `crates/`

**Postinstall**:
- `omx setup` registers hooks, installs prompts, scaffolds `.omx/` + `AGENTS.md`
- Plugin setup mode uses `.agents/plugins/marketplace.json` for discovery

---

## Execution Modes

| Mode | Launch | Workers | State | Use case |
|------|--------|---------|-------|----------|
| **Direct** | `omx --direct` | 1 | Session `.omx/` | One-off, no tmux |
| **Detached tmux** | `omx --detached-tmux` (default) | 1 | Session `.omx/` + HUD pane | Long-running with UI |
| **Team** | `omx team 3:executor` | N | Team `.omx/team/` | Parallel multi-agent |
| **Ralph** | `$ralph "..."` (inside Codex) | 1 | Ralph ledger | Persistent loop |
| **Ultragoal** | `$ultragoal "..."` | 1 | Goal ledger | Durable goals |

---

## Config & Customization

**Setup files** (after `omx setup`):
- `.codex/config.toml` — Codex model/auth config
- `.codex/hooks.json` — Native hook registrations (legacy/fallback)
- `plugins/oh-my-codex/hooks/hooks.json` — Plugin hook registrations (preferred)
- `.omx/state/` — Runtime state
- `AGENTS.md` — Project guidance (role + instruction templates)
- `.omx/hooks/*.mjs` — User hook plugins

**Environment overrides**:
- `OMX_LAUNCH_POLICY=direct|tmux|detached-tmux|auto` — Default launch mode
- `OMX_AUTO_UPDATE=0|defer` — Auto-update behavior
- `OMX_RUNTIME_BRIDGE=0` — Disable Rust bridge (use TS-direct)
- `CODEX_HOME` — Codex config directory
- `DISCORD_STATE_DIR` — Discord bot state (for Discord integration)

---

## Summary

**oh-my-codex** is a sophisticated orchestration platform that:

1. **Orchestrates** Codex CLI with workflows (autopilot FSM) and multi-agent team execution
2. **Persists** durable state in `.omx/` using JSON + file locking, with event-sourced dispatch via Rust
3. **Coordinates** workers via tmux panes, file-based task queues, and inter-worker messaging
4. **Manages** auth rotation to avoid quota limits
5. **Extends** via plugin hooks that intercept Codex lifecycle events
6. **Renders** real-time HUD + sidecar for visibility
7. **Integrates** with MCP as optional compatibility (CLI/JSON is canonical)

The architecture favors durability (crash recovery), auditability (JSON state), and **CLI-first automation** over complex abstractions. Team mode is the flagship feature, enabling coordinated parallel agent execution with recovery semantics.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `crates/omx-runtime-core/src/engine.rs` | State machine, event processing |
| `crates/omx-mux/src/lib.rs` | Tmux contract definitions |
| `src/cli/index.ts` | Main CLI dispatcher |
| `src/team/orchestrator.ts` | Team phase state machine |
| `src/autopilot/fsm.ts` | Workflow phase enumeration |
| `src/runtime/bridge.ts` | Rust omx-runtime wrapper |
| `src/state/operations.ts` | State mutation entry points |
| `src/auth/rotation.ts` | Token rotation logic |
| `src/hud/state.ts` | HUD context builder |
| `src/sidecar/collector.ts` | Team state snapshot |
| `src/hooks/keyword-detector.ts` | Skill keyword parsing |
| `docs/contracts/multi-state-transition-contract.md` | Active workflow combination rules |
| `docs/architecture/cli-first-mcp-taxonomy.md` | CLI vs MCP authority |
