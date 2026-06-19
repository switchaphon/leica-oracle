# oh-my-codex (OMX) Architecture — Deep Analysis

**Document Date**: 2026-06-19  
**Repository Version**: 0.18.13  
**Analysis Scope**: Full architecture, runtime mechanics, state management, team orchestration

---

## Executive Summary

**oh-my-codex** is a sophisticated **orchestration and workflow management layer** built on top of OpenAI's Codex CLI. It transforms Codex from a single-agent tool into a multi-agent, durable, stateful system for complex software engineering tasks.

**Core thesis**: Codex executes work; OMX orchestrates it through:
- **Workflow phases** (autopilot FSM: deep-interview → ralplan → ultragoal → team → ralph → code-review → ultraqa)
- **Durable state** (file-based JSON in `.omx/state/`, event-sourced via Rust runtime)
- **Multi-agent coordination** (tmux-based team mode with task queues, messaging, and phase synchronization)
- **Authority leasing** (prevents concurrent mutations; enables crash recovery and worker handoff)
- **Credential rotation** (manages multiple API keys to avoid quota exhaustion)
- **Hook system** (intercepts Codex lifecycle events for context injection, triage, and custom actions)

---

## Architecture Layers

### 1. **Rust Runtime (`crates/`)**

The Rust layer provides **durable, crash-recoverable state management** and **type-safe tmux operations**.

#### Workspace Structure (v0.18.13)

```
crates/
├── omx-api/               # JSON schema definitions for inter-process contracts
├── omx-explore/           # Full codebase explorer (parallel to omx-sparkshell)
├── omx-explore-harness/   # Build harness for omx-explore
├── omx-mux/               # Tmux abstraction layer
├── omx-runtime-core/      # State machine engine
├── omx-runtime/           # CLI binary wrapping omx-runtime-core
└── omx-sparkshell/        # Lightweight repo scanner (fallback model support)
```

#### omx-mux: Tmux Abstraction

**Purpose**: Type-safe, serializable tmux operations for agent isolation and HUD rendering.

**Key exports**:
- `TmuxAdapter` — executes tmux send-input, capture-pane, attach, detach
- `MuxOperation` enum — serializable command set
- `SubmitPolicy` — defines Enter key count and delay (handles batch input buffering)
- `ConfirmationPolicy` — verification strategies (check output, verify LLM parsing, etc.)
- `InputEnvelope` — normalized text + submit rules

**Guarantee**: All operations are JSON-roundtrip safe. Enables JSON-over-stdio IPC from Node.js to Rust.

**Operation set**:
- `resolve-target` — Map pane alias to tmux coordinates
- `send-input` — Deliver text with retry + confirmation
- `capture-tail` — Read last N lines from pane
- `inspect-liveness` — Check if pane/session alive
- `attach / detach` — Enter/exit tmux

---

#### omx-runtime-core: State Machine & Authority

**Purpose**: Durable, replayed, authority-leased runtime state machine for dispatch and inter-worker messaging.

**Core modules**:

1. **authority.rs** — File-based lease acquisition/renewal
   - Exclusive write access guard
   - Lease TTL (e.g., `leased_until: 2026-06-19T14:00:00Z`)
   - On leader crash: another process can acquire after TTL expires

2. **engine.rs** — State machine processor
   - Input: `RuntimeCommand` enum (AcquireAuthority, QueueDispatch, MarkDelivered, CreateMailboxMessage, etc.)
   - Processing: Validates command, transitions state, produces events
   - Output: `RuntimeEvent` enum (AuthorityAcquired, DispatchQueued, DispatchDelivered, etc.)
   - Persistence: Events appended to journal; state replayed from journal on boot

3. **dispatch.rs** — Task queue with delivery confirmation
   - States: pending → notified → delivered / failed
   - Owned by a specific `request_owner` (worker name)
   - Timeout: if not delivered by deadline, mark failed

4. **mailbox.rs** — Inter-worker messaging
   - Bidirectional message queues per worker pair
   - Used for: task handoff, coordination, conflict resolution

5. **replay.rs** — Crash recovery
   - Reads event journal from disk
   - Replays all events to reconstruct current state
   - Allows resuming from point of crash

**State machine diagram**:
```
Command (e.g., QueueDispatch)
  ↓
RuntimeEngine.process(cmd, state)
  ↓
Validate (is authority held? is this dispatch already delivered?)
  ↓
Produce Event (DispatchQueued)
  ↓
Persist Event to journal
  ↓
Return Event to caller
```

**Key invariant**: Authority is a **lease**. Commands from non-current-owner fail unless the lease has expired.

---

#### omx-runtime: CLI Binary

**Purpose**: Expose runtime state machine operations via JSON CLI.

**Commands**:
```bash
omx-runtime schema [--json]
  → Print Rust type definitions (JSON schema)

omx-runtime snapshot [--state-dir=.omx/state/session-abc]
  → Read current state: authority, dispatch queue, replay journal

omx-runtime mux-contract
  → Print MuxOperation enum schema

omx-runtime exec '<json-command>' [--state-dir=.omx/state/session-abc] [--compact]
  → Parse JSON command, process via engine, return JSON event
```

**Example**:
```bash
omx-runtime exec '{
  "command": "AcquireAuthority",
  "owner": "leader-1",
  "lease_id": "lease-abc123",
  "leased_until": "2026-06-19T14:00:00Z"
}'
```

**Contract**: All input/output is JSON. State is **only persisted if `--state-dir` is provided**.

---

#### omx-sparkshell: Lightweight Explorer

**Purpose**: Fast, cost-optimized repository summary for context injection into Codex.

**Use case**: `omx explore --prompt "..."` for read-only repo analysis (summary tokens < full omx-explore).

**Features**:
- Redaction of secrets before output
- Fallback model support (cheaper LLM for preliminary scans)
- Codex subprocess bridge

---

#### omx-explore: Full Explorer

**Purpose**: Comprehensive codebase mapping (parallel to omx-sparkshell, more capable).

---

### 2. **TypeScript/Node.js Layer (`src/`)**

The Node.js layer orchestrates Codex execution, manages state transitions, handles team coordination, and provides CLI/MCP interfaces.

#### Directory Structure

```
src/
├── cli/
│   ├── omx.ts                    # ES module shim, entry point
│   ├── index.ts                  # Main dispatcher, argument parsing
│   ├── setup.ts                  # Initialize .omx/, install hooks
│   ├── uninstall.ts              # Teardown OMX from project
│   ├── team.ts                   # Team spawn/lifecycle commands
│   ├── ralph.ts                  # Persistent loop command
│   ├── ultragoal.ts              # Multi-goal execution command
│   ├── state.ts                  # Read/write durable state
│   ├── hooks.ts                  # Hook lifecycle management
│   ├── tmux-hook.ts              # Tmux runtime hook entry point
│   ├── codex-home.ts             # Codex config discovery
│   ├── ask.ts                    # Direct question to Codex
│   ├── agents-init.ts            # Initialize AGENTS.md
│   ├── agents.ts                 # Manage AGENTS.md per scope
│   ├── session-search.ts         # Find/resume sessions
│   ├── adapt.ts                  # Adapt projects to OMX
│   ├── auth.ts                   # Auth slot management
│   └── __tests__/                # CLI tests
├── team/
│   ├── orchestrator.ts           # Team phase state machine
│   ├── state.ts                  # TeamConfig, WorkerInfo, TeamTask
│   ├── state/
│   │   ├── tasks.ts              # Task claim logic + readiness
│   │   ├── mailbox.ts            # Inter-worker messaging
│   │   ├── dispatch.ts           # Dispatch queue
│   │   └── locks.ts              # File-based locking
│   ├── coordination-protocol.ts  # Plan sharing between workers
│   ├── worker-bootstrap.ts       # Spawn worker with context
│   ├── tmux-session.ts           # Tmux session lifecycle
│   ├── worktree.ts               # Git worktree management
│   └── __tests__/                # Team tests
├── autopilot/
│   ├── fsm.ts                    # Phase enumeration + state derivation
│   ├── deep-interview-gate.ts    # Validate transition to ralplan
│   ├── ralplan-gate.ts           # Validate transition to ultragoal
│   └── (other gates)
├── runtime/
│   ├── bridge.ts                 # Rust omx-runtime wrapper
│   ├── auth.ts                   # Codex auth interaction
│   ├── session.ts                # Session state reading
│   ├── run-outcome.ts            # Execution result classification
│   └── __tests__/
├── auth/
│   ├── index.ts                  # Auth slot lifecycle
│   ├── rotation.ts               # Round-robin/priority rotation
│   ├── hotswap.ts                # Token swap during execution
│   ├── quota-detector.ts         # Rate-limit detection
│   ├── storage.ts                # Persistent slot records
│   └── __tests__/
├── state/
│   ├── paths.ts                  # .omx/ directory layout
│   ├── operations.ts             # State mutation entry points
│   ├── skill-active.ts           # Active workflow tracking
│   ├── workflow-transition.ts    # Approval/denylist for mode combinations
│   ├── mode-state-context.ts     # Mode-specific state access
│   └── __tests__/
├── hud/
│   ├── state.ts                  # HUD rendering context builder
│   ├── index.ts                  # HUD command dispatcher
│   ├── authority.ts              # Authority lease display
│   ├── reconcile.ts              # HUD sync with tmux
│   ├── constants.ts              # Layout dimensions
│   ├── types.ts                  # Type definitions
│   └── __tests__/
├── sidecar/
│   ├── collector.ts              # Gather team state snapshot
│   ├── render.ts                 # Format as TUI
│   ├── tmux.ts                   # Sidecar pane management
│   ├── types.ts                  # Data structures
│   └── __tests__/
├── mcp/
│   ├── state-server.ts           # MCP server for state mutations
│   ├── trace-server.ts           # Event tracing MCP
│   ├── state-paths.ts            # Session/scope resolution
│   └── __tests__/
├── hooks/
│   ├── keyword-detector.ts       # Parse $skill keywords (e.g., $ultragoal)
│   ├── agents-overlay.ts         # Inject AGENTS.md context
│   ├── triage-heuristic.ts       # Estimate task complexity
│   ├── codebase-map.ts           # Fast static repo snapshot
│   ├── session.ts                # Session lifecycle tracking
│   ├── notify-*.ts               # Various notification hooks
│   ├── extensibility/
│   │   └── plugin-runner.ts      # Load + execute user hook plugins
│   └── __tests__/
├── ralph/
│   ├── persistence.ts            # Durable loop ledger
│   ├── completion-audit.ts       # Verify completion state
│   └── __tests__/
├── ultragoal/
│   ├── context.ts                # Goal ledger management
│   └── (other structures)
├── config/
│   ├── generator.ts              # Generate/repair Codex config
│   ├── mcp-registry.ts           # MCP server registration
│   ├── omx-first-party-mcp.ts    # OMX-shipped MCP servers
│   └── __tests__/
├── utils/
│   ├── paths.ts                  # Path utilities
│   ├── package.ts                # Package introspection
│   ├── toml.ts                   # TOML parsing/writing
│   └── __tests__/
├── scripts/
│   ├── postinstall.js            # npm postinstall hook
│   ├── setup-hooks-shared-ownership.js
│   ├── build-*.js                # Build scripts (explore, sparkshell, api)
│   ├── verify-native-agents.js   # Validate native agent definitions
│   ├── sync-plugin-mirror.js     # Sync plugin registry
│   ├── generate-catalog-docs.js  # Auto-generate docs from catalog
│   └── __tests__/
├── catalog/
│   ├── index.ts                  # Catalog of skills/prompts
│   └── __tests__/
└── index.ts                      # Main export for module usage
```

---

## Core Abstractions

### 1. **Autopilot FSM** (`src/autopilot/fsm.ts`)

Enforces a **strict, ordered sequence of workflow phases**.

```typescript
const AUTOPILOT_PHASES = [
  'deep-interview',   // Clarify scope, ask clarifying questions
  'ralplan',          // Approve architecture/plan
  'ultragoal',        // Durable multi-goal execution
  'team',             // Coordinated parallel execution
  'ralph',            // Persistent loop (retry on failure)
  'code-review',      // Verification pass
  'ultraqa',          // Testing/validation
  // Terminal states:
  'waiting-for-user', // Paused, waiting for input
  'complete',         // Success
  'failed',           // Failed (no recovery)
];
```

**Key functions**:
- `isAutopilotChildPhase(value)` — Type guard
- `deriveAutopilotChildPhase(state)` — Read current phase from state JSON
- `normalizeAutopilotPhase(value)` — Parse and normalize user input
- `isAutopilotSupervising(state)` — Is autopilot active?

**Invariant**: Cannot skip phases or go backward (except ralph loop within ultragoal). Enforced via `isNextAutopilotPhase()`.

**Phase validation gates** (in `src/autopilot/`):
- `deep-interview-gate.ts` — Check scope clarity before ralplan
- `ralplan-gate.ts` — Check plan approval before ultragoal
- etc.

---

### 2. **Team Orchestration** (`src/team/orchestrator.ts`)

Manages multi-agent execution with **phase-based task coordination**.

```typescript
type TeamPhase = 'team-plan' | 'team-prd' | 'team-exec' | 'team-verify' | 'team-fix';
type TerminalPhase = 'complete' | 'failed' | 'cancelled';

interface TeamState {
  active: boolean;
  phase: TeamPhase | TerminalPhase;
  task_description: string;
  created_at: string;
  phase_transitions: Array<{ from, to, at, reason? }>;
  tasks: TeamTask[];
  max_fix_attempts: number;
  current_fix_attempt: number;
}
```

**Phase machine**:
```
team-plan
  ↓ (requirements clear, tasks defined)
team-prd
  ↓ (PRD approved, execution plan ready)
team-exec
  ↓ (all tasks done)
team-verify
  ↓
  ├→ team-fix (if issues found, retry up to max_fix_attempts)
  │   ↓
  │   └→ team-exec (loop back)
  │
  └→ complete / failed (terminal)
```

**Per-phase agents** (from `getPhaseAgents(phase)`):
- `team-plan` → analyst, planner
- `team-prd` → product-manager, analyst
- `team-exec` → executor, designer, test-engineer
- `team-verify` → verifier, code-reviewer, quality-reviewer
- `team-fix` → executor, debugger, test-engineer

**Phase instructions** (from `getPhaseInstructions(phase)`):
- Each phase has specific agent roles + expected output format
- Injected into AGENTS.md context for Codex

**Worker lifecycle**:
1. Leader spawns N workers via `tmux new-window`
2. Each worker gets dedicated worktree + task queue
3. Workers claim tasks via `omx team api claim-task --json`
4. On completion, mark task done, leader transitions phase
5. If team-fix needed, leader re-assigns failing tasks

---

### 3. **Durable State Management** (`src/state/`, `src/mcp/state-paths.ts`)

All runtime state lives in `.omx/state/{scope}/` as JSON files.

#### State Root & Scopes

**Base directory**: `.omx/state/`

**Scopes** (resolved from session ID + mode):
- Standalone session: `.omx/state/session-{uuid}/`
- Team session: `.omx/state/team-{team-name}/`

#### Per-Scope State Files

| File | Purpose | Owned By |
|------|---------|----------|
| `autopilot-state.json` | Autopilot phase + deep-interview questions | Autopilot FSM |
| `ralph-state.json` | Persistent loop ledger (attempts, outcomes) | Ralph mode |
| `ultragoal-state.json` | Multi-goal plan + per-goal status | Ultragoal mode |
| `skill-active-state.json` | **Canonical active workflow set** | Skill transition validator |
| `{mode}-state.json` | Any other mode-specific data | That mode |
| `team-state.json` | Team phase + tasks + workers | Team orchestrator |

#### skill-active-state.json: Workflow Validity

**Format**:
```json
{
  "mode": "autopilot",
  "active": true,
  "active_skills": ["deep-interview"],
  "approved_parallel_modes": ["mcp"]
}
```

**Purpose**: Enforce that incompatible workflows don't run simultaneously.
- `autopilot` + `team` simultaneously? ❌
- `autopilot` + `mcp` (MCP server for state inspection)? ✅

**Validation**: `src/state/workflow-transition.ts` defines transition rules via `isNextAutopilotPhase()` and mode compatibility checks.

---

### 4. **Runtime Bridge** (`src/runtime/bridge.ts`)

TypeScript wrapper over the Rust `omx-runtime` binary for durable state mutations.

**Flow**:
```
TS wants to queue a dispatch
  ↓
bridge.execCommand({ command: 'QueueDispatch', request_id, target }, stateDir)
  ↓
Spawn: omx-runtime exec '<json>' --state-dir=stateDir
  ↓
Rust engine processes, returns JSON event
  ↓
TS receives RuntimeEvent (e.g., DispatchQueued)
  ↓
TS can proceed knowing state is durable
```

**Types** (mirror Rust types):
- `RuntimeSnapshot` — read authority + dispatch + mailbox state
- `RuntimeCommand` — mutations
- `RuntimeEvent` — outcomes
- `DispatchRecord` — per-dispatch metadata
- `MailboxRecord` — inter-worker message

**Fallback**: `OMX_RUNTIME_BRIDGE=0` env var disables Rust bridge, uses TS-direct fallback.

---

### 5. **Auth Rotation** (`src/auth/`)

Manages multiple API keys to avoid quota limits.

**Slot management** (`auth/index.ts`):
- Each slot has: name, API key, rate-limit metadata, last-used timestamp
- Slots stored in `.omx/auth/slots.json`

**Rotation strategies** (`auth/rotation.ts`):
- `"manual"` — Use specified slot only
- `"round-robin"` — Cycle through all slots evenly
- `"priority"` — Primary slot, fallback to others

**Flow**:
1. Build rotation plan from slots + strategy
2. Before each Codex invocation: `nextSlotAfter(current, exhausted_slots)`
3. Swap `OPENAI_API_KEY` or `CODEX_API_KEY` env var
4. Spawn Codex subprocess with new key
5. Update slot metadata on completion

**Quota detection** (`auth/quota-detector.ts`):
- Monitor Codex output for rate-limit signatures
- Mark slot exhausted, move to next

---

### 6. **Hook System** (`src/hooks/`)

Intercepts Codex lifecycle events to inject context, detect intent, and trigger custom actions.

#### Hook Entry Points

1. **Codex native hooks** (in `.codex/config.toml` or plugin registry)
   - Trigger at Codex startup, before each model call, on completion
   - Configured via `setup` command

2. **OMX plugin hooks** (in `.omx/hooks/*.mjs`)
   - User-defined ES modules
   - Loaded by `plugin-runner.ts`

3. **Fallback hooks**
   - Built-in watchers (notify-hook, tmux-hook) if native hooks unavailable

#### Key Hooks

**keyword-detector.ts**
- Parses skill keywords: `$ultragoal`, `$deep-interview`, `$ralplan`, `$team "..."`, `$ralph "..."`
- Extracts intent, delegates to skill handler

**agents-overlay.ts**
- Generates AGENTS.md scoped to current phase + mode
- Injects agent role definitions + phase instructions
- Reads from `src/catalog/` + `skills/` directory

**triage-heuristic.ts**
- Estimates task complexity (lines of code, dependencies, etc.)
- Used to recommend mode (direct vs team, phase length, etc.)

**codebase-map.ts**
- Fast static repository snapshot (AST scans, dependency graph)
- Injected as context for Codex

**explore-routing.ts**
- Routes `$omx-explore` keyword to omx-explore or sparkshell fallback
- Decides based on cost/quality tradeoff

---

### 7. **HUD (Heads-Up Display)** (`src/hud/`)

Real-time rendering of runtime state in a dedicated tmux pane.

**Context** (`HudRenderContext`):
```typescript
interface HudRenderContext {
  version: string;
  cwd: string;
  gitDisplay: GitDisplay;
  session: {
    phase: AutopilotRuntimePhase;
    activeWorkflows: string[];
  };
  team?: {
    phase: TeamPhase | TerminalPhase;
    workerCount: number;
    taskSummary: { pending, claimed, done };
  };
  ralph?: { completionPercent };
  ultragoal?: { activeGoals, progress };
  metrics: { timestamp, uptime, notificationCount };
}
```

**Presets**:
- `minimal` — One-line status
- `focused` — Current phase + key metrics
- `full` — All state + worker/task details

**Refresh**: Polled from `.omx/state/` files on 1s interval (configurable).

**Tmux lifecycle**:
- Leader spawns HUD in `--tmux` mode: `omx <cmd> --tmux`
- HUD pane created via `tmux new-window`
- HUD runs watch loop, updates on state changes
- On window resize, HUD re-layouts

**resize-hook** (`src/team/tmux-session.ts`):
- Intercepts `signal_resize` from Codex
- Notifies HUD of new dimensions
- HUD reflows content

---

### 8. **Sidecar** (`src/sidecar/`)

Optional right-side tmux pane for **team monitoring** (complementary to main HUD).

**Flow**:
```
omx sidecar <team-name> --tmux
  ↓
collectSidecarSnapshot() → read .omx/team/{team}/state/
  ↓
renderSidecar() → format TUI (worker boxes, task assignments)
  ↓
launchSidecarTmuxPane() → create new pane, run watch loop
  ↓
Every 1s: update snapshot, re-render
```

**Output**: Worker list with:
- Worker name + status (idle, working, done)
- Assigned task + progress
- Error messages (if any)
- Team phase + overall progress bar

---

## Data Flows

### Example 1: `$ultragoal "Build Auth Handler"`

**User types**:
```
$ultragoal "Build the authentication handler for OAuth2"
```

**Path**:
```
1. Codex CLI receives input
2. Hook: keyword-detector.ts parses $ultragoal + intent
3. Hook: agents-overlay.ts injects ultragoal-phase instructions
4. Codex spawns LLM with context
5. LLM response read by hook
6. Hook: transitionUltragoalState() → record goal in .omx/ultragoal-state.json
7. HUD: reads ultragoal-state.json, displays goal + progress
8. LLM executes goal (may spawn sub-Codex calls)
9. On completion: hook marks goal done in ledger
10. HUD: displays next goal (if any) or completion
```

---

### Example 2: `omx team 3:executor "Split auth + payments across 3 workers"`

**Command**:
```bash
omx team 3:executor "Split auth + payments across 3 workers"
```

**Execution**:

```
1. CLI: team.ts dispatcher
2. Create tmux session: omx-team-{unique-id}
3. Create leader pane (main process) + 3 worker panes
4. Initialize .omx/team/{team-name}/state/:
   - team-state.json (phase: team-plan)
   - tasks.json (empty)
   - workers.json (3 workers, idle)
5. LEADER → TEAM-PLAN PHASE:
   - Spawn Codex in leader pane
   - Codex: "Break down this task into 3 independent tasks"
   - LLM output: 3 task definitions
   - Transition to team-prd
6. LEADER → TEAM-PRD PHASE:
   - PRD approval loop (human confirms tasks)
   - Transition to team-exec
7. LEADER → TEAM-EXEC PHASE:
   - Queue 3 tasks in dispatch queue
   - WORKERS claim tasks:
     - Worker-1 calls: omx team api claim-task
     - Runtime: assigns task-1 (auth), marks claimed
     - Worker-1 spawns Codex subprocess → works on task
     - On done: mark delivered
   - (Similar for worker-2, worker-3)
   - Leader monitors delivery; when all done → team-verify
8. LEADER → TEAM-VERIFY PHASE:
   - Run test suite, check coverage
   - If failures: transition to team-fix
     - Re-assign failing tasks
     - max_fix_attempts: 3
   - If success: transition to complete
9. SIDECAR pane displays entire timeline:
   - Phase transitions
   - Worker progress
   - Task assignments
   - Error logs
```

---

### Example 3: `$ralph "Debug the failing integration test"`

**User types**:
```
$ralph "Debug the failing integration test"
```

**Execution**:

```
1. Codex: Parse $ralph keyword
2. Enter ralph mode (persistent loop)
3. Initialize .omx/ralph-state.json:
   - task: "Debug the failing integration test"
   - attempts: []
4. ATTEMPT #1:
   - Codex executes task
   - Read test output / error
   - Record outcome in attempts[0]
5. Check: did test pass?
   - Yes → update attempts[0].status = done → exit ralph
   - No → ask user: "Should I retry? (y/n)"
     - If y: attempt #2
     - If n: exit (status: manual-stop)
6. ralph-persistence.ts:
   - On resume: read ralph-state.json, continue from where left off
   - Replays all prior attempts for context
7. On success: mark complete, persist ledger
```

---

## Execution Modes

| Mode | Entry | Workers | State | Use Case |
|------|-------|---------|-------|----------|
| **Direct** | `omx --direct` | 1 | `.omx/state/session-{id}/` | One-off, no UI |
| **Detached tmux** (default) | `omx` or `--detached-tmux` | 1 | `.omx/state/session-{id}/` + HUD pane | Long-running with HUD |
| **Team** | `omx team N` | N | `.omx/state/team-{name}/` + Sidecar | Parallel multi-agent |
| **Ralph** | `$ralph "..."` inside Codex | 1 | `.omx/ralph-state.json` | Persistent retry loop |
| **Ultragoal** | `$ultragoal "..."` | 1 | `.omx/ultragoal-state.json` | Multi-goal durable execution |

---

## State Mutation Authority

**All durable state writes** go through one of:

### 1. **Rust Bridge** (preferred)

```typescript
const event = await bridge.execCommand(
  { command: 'QueueDispatch', request_id: 'req-1', target: 'worker-1' },
  stateDir
);
// event: { status: 'DispatchQueued', dispatch_record: {...} }
```

**Advantages**:
- Crash-safe (event-sourced)
- Concurrent-write safe (authority lease)
- Replay recovery

### 2. **TS-Direct** (legacy fallback)

```typescript
await writeStateFile(path, data);
```

Disabled via `OMX_RUNTIME_BRIDGE=0`.

### 3. **MCP** (compatibility layer)

```typescript
omx_state.state_write({ mode: 'team', data: {...} })
```

Optional; CLI/JSON is canonical.

---

## Setup & Initialization

### `omx setup`

Initializes OMX in a project:

1. **Scaffold `.omx/` directory**:
   - `.omx/state/` — Runtime state
   - `.omx/auth/` — Auth slots
   - `.omx/hooks/` — User hook plugins
   - `.omx/catalog/` — Skills/prompts cache

2. **Register Codex hooks**:
   - Write to `.codex/config.toml` OR `plugins/oh-my-codex/hooks/hooks.json`
   - Hook entry points: before-model-call, after-completion, etc.

3. **Initialize `AGENTS.md`**:
   - Generates default agent role definitions
   - Each role gets personality + instructions
   - Scoped to project + phase

4. **Create `.codex/` if missing**:
   - Copy default `config.toml`
   - Register MCP servers (optional)

### `omx doctor`

Validates setup:
- `.omx/` directory exists and writable
- Codex config reachable
- Hooks registered
- Git worktree support
- Tmux available (if tmux mode used)

---

## Environment Variables & Config

### Environment Overrides

| Variable | Default | Purpose |
|----------|---------|---------|
| `OMX_LAUNCH_POLICY` | `detached-tmux` | Launch mode: direct / tmux / detached-tmux / auto |
| `OMX_AUTO_UPDATE` | `enabled` | Auto-update behavior: enabled / defer / disabled |
| `OMX_RUNTIME_BRIDGE` | `1` | Use Rust bridge (0 = TS-direct fallback) |
| `CODEX_HOME` | `~/.codex` | Codex config directory |
| `DISCORD_STATE_DIR` | `.discord-state/` | Discord bot state (if Discord integration enabled) |
| `OMX_TMUX_HUD_OWNER_ENV` | (computed) | HUD ownership tracking |

### Config Files

After `omx setup`:
- `.codex/config.toml` — Codex model, auth, MCP registrations
- `.codex/hooks.json` — Native hook registrations (legacy)
- `plugins/oh-my-codex/hooks/hooks.json` — Plugin hook registrations (preferred)
- `.omx/state/` — Runtime state
- `AGENTS.md` — Project agent guidance

---

## Build & Distribution

### Build Steps

```bash
npm run build                # Compile TS → dist/
npm run build:sparkshell     # Build omx-sparkshell Rust binary
npm run build:api            # Build API schema
npm run build:full           # All of above + omx-explore
```

### Distribution

- Published to npm: `npm install -g oh-my-codex`
- Also available as Codex plugin: `plugins/oh-my-codex/`
- Native binaries (sparkshell, explore) bundled in npm tarball under `crates/`

### Postinstall

```bash
npm postinstall
→ node dist/scripts/postinstall.js
→ omx setup (auto-runs, user can skip)
```

---

## Key Design Patterns

### 1. **File-Based State, JSON-Serialized**

**Why**: 
- Inspectable (cat .omx/state/session-xxx/ultragoal-state.json)
- Debuggable (read history via git diff)
- Simple (no database, no network)

**Trade-off**: Slower than in-memory, but durability + crash recovery worth it.

### 2. **Event Sourcing for Authority & Dispatch**

**Why**:
- Immutable event journal
- Replay from crash point
- Authority lease prevents concurrent writes

**Pattern** (Rust engine):
- Events immutable once written
- Journal append-only
- State derived from replaying all events

### 3. **Tmux as Execution Fabric**

**Why**:
- Each agent gets isolated pane
- Output capture is built-in (tmux capture-pane)
- Multi-pane HUD overlays native
- No need for custom IPC (use text + tmux)

### 4. **CLI-First Control Plane**

**Why**:
- Stateless CLI (OMX orchestrates)
- Stateful agent (Codex executes)
- JSON automation surfaces
- MCP optional (not required for runtime)

### 5. **Strict Phase Ordering (Autopilot FSM)**

**Why**:
- Prevents user mistakes (can't skip planning)
- Enforces workflow discipline
- Testable (phase transitions exhaustively checked)

### 6. **Authority Leasing for Multi-Worker Coordination**

**Why**:
- Prevents concurrent writes (only one authority owner)
- Enables crash recovery (lease expires, next leader can takeover)
- No SPOF (distributed authority)

---

## Comparison: OMX vs. Codex CLI

| Aspect | Codex CLI | OMX + Codex |
|--------|-----------|------------|
| **State** | In-memory, ephemeral | Durable JSON in .omx/ |
| **Multi-agent** | Single agent | Multiple coordinated agents |
| **Workflows** | Unstructured | Autopilot FSM (phases) |
| **Crash recovery** | None | Replay from event journal |
| **Credential mgmt** | Single key | Multiple slots, rotation |
| **Hooks/extensions** | Limited | Rich hook system + plugins |
| **Team mode** | Not supported | Full team orchestration |
| **HUD/monitoring** | None | Real-time HUD + sidecar |

---

## Relationship to maw (Multi-Agent Workflow)

**maw** is Leica's tmux-based orchestrator for spawning agents directly.

**Relationship**:
- **maw** spawns agents as tmux panes + manages IPC
- **OMX** wraps Codex CLI with state machine + workflow phases
- **Complementary**: maw used for ad-hoc agent spawning; OMX used for durable, stateful workflows

**When to use**:
- `maw` → Quick multi-agent task (no state recovery needed)
- `OMX` → Long-running complex workflows (needs crash recovery, phase tracking)

---

## Future Directions (from code hints)

Based on `.gjc/`, `src/catalog/`, and test files:

1. **Geobench profiles** — Standardized model profiling for recommendations
2. **Project resume/search** — Better discovery of active sessions
3. **Improved ralph consensus** — Better convergence for persistent loops
4. **HUD state reconciliation** — Fixing edge cases in HUD sync
5. **Cross-platform team mode** — Better Windows/WSL support

---

## Summary Table: Files & Their Roles

| File | Role | Responsibility |
|------|------|-----------------|
| `crates/omx-runtime-core/src/engine.rs` | State machine | Event processing, authority, dispatch |
| `crates/omx-mux/src/lib.rs` | Tmux contract | Serializable tmux operations |
| `src/cli/index.ts` | CLI dispatcher | Argument parsing, command routing |
| `src/autopilot/fsm.ts` | Workflow phases | Phase enumeration + transitions |
| `src/team/orchestrator.ts` | Team FSM | Team phase machine + agent assignment |
| `src/team/state.ts` | Team state | TeamConfig, WorkerInfo, TeamTask |
| `src/runtime/bridge.ts` | Rust IPC | Invoke omx-runtime binary |
| `src/state/operations.ts` | State mutations | Write .omx/ files (legacy) |
| `src/state/skill-active.ts` | Workflow validity | Track active modes, prevent conflicts |
| `src/auth/rotation.ts` | Credential mgmt | API key rotation strategy |
| `src/hooks/keyword-detector.ts` | Skill parsing | Parse $ultragoal, $team keywords |
| `src/hooks/agents-overlay.ts` | Context injection | Generate AGENTS.md for phase |
| `src/hud/state.ts` | HUD context | Build rendering context |
| `src/sidecar/collector.ts` | Team monitoring | Snapshot team state for sidecar |
| `src/mcp/state-server.ts` | MCP compat | State mutations via MCP |
| `src/ralph/persistence.ts` | Ralph loops | Durable retry ledger |

---

## Conclusion

**oh-my-codex** is a **durable, scalable, crash-recoverable orchestration platform** that transforms Codex from a single-agent tool into a **coordinated multi-agent system**. Its architecture prioritizes:

1. **Durability** — All state persisted; crash recovery via event replay
2. **Auditability** — JSON state on disk; git-friendly diffs
3. **Composability** — Modular phases (autopilot FSM) + team modes
4. **Extensibility** — Hook system + plugin architecture
5. **CLI-first** — JSON automation surfaces; MCP optional

The **Rust layer** (omx-runtime-core) provides crash-safe, leased authority; the **Node.js layer** orchestrates Codex execution, state transitions, and team coordination via tmux.

**Result**: Complex, long-running multi-agent workflows can survive crashes, coordinate workers, and progress durable goals without human re-intervention.

