# oh-my-codex — Code Reference & Quick Guide

**Date**: 2026-06-19  
**Version**: 0.18.13

---

## Autopilot FSM Phase Sequence

```typescript
// src/autopilot/fsm.ts
const AUTOPILOT_PHASES = [
  'deep-interview',    // Gather requirements, clarify scope
  'ralplan',           // Architecture review + approval
  'ultragoal',         // Durable multi-goal execution
  'team',              // Coordinated multi-agent work
  'ralph',             // Persistent retry loop
  'code-review',       // Verification pass
  'ultraqa',           // Testing + validation
  // Terminal:
  'waiting-for-user',  // Paused, awaiting input
  'complete',          // Success
  'failed',            // Unrecoverable failure
];

// Phase transitions are strictly ordered
// Cannot skip phases or go backward (except ralph loop within ultragoal)
```

---

## Team Orchestration Phase Machine

```typescript
// src/team/orchestrator.ts
type TeamPhase = 'team-plan' | 'team-prd' | 'team-exec' | 'team-verify' | 'team-fix';

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

// Transitions:
// team-plan -> team-prd -> team-exec -> team-verify 
//                                           ├-> team-fix (loop to team-exec)
//                                           └-> complete / failed

// Per-phase agent roles:
function getPhaseAgents(phase: TeamPhase): string[] {
  switch (phase) {
    case 'team-plan':      return ['analyst', 'planner'];
    case 'team-prd':       return ['product-manager', 'analyst'];
    case 'team-exec':      return ['executor', 'designer', 'test-engineer'];
    case 'team-verify':    return ['verifier', 'code-reviewer', 'quality-reviewer'];
    case 'team-fix':       return ['executor', 'debugger', 'test-engineer'];
  }
}
```

---

## State Path Resolution

```typescript
// src/mcp/state-paths.ts
// .omx/state/ layout:

// Standalone session (single agent)
.omx/state/session-{uuid}/
  ├── autopilot-state.json        // Autopilot FSM state
  ├── ultragoal-state.json        // Goals + progress
  ├── ralph-state.json            // Persistent loop attempts
  └── skill-active-state.json     // Active workflow set

// Team session (multi-agent)
.omx/state/team-{team-name}/
  ├── team-state.json             // Team FSM phase
  ├── tasks.json                  // Task queue
  ├── workers.json                // Worker info + assignments
  └── mailbox.json                // Inter-worker messages

// Canonical active workflow set:
.omx/state/{scope}/skill-active-state.json
{
  "mode": "autopilot",            // Currently active mode
  "active": true,
  "active_skills": ["deep-interview"],
  "approved_parallel_modes": ["mcp"]  // Allowed concurrent modes
}
```

---

## Runtime Bridge Execution

```typescript
// src/runtime/bridge.ts
// All durable state writes go through Rust omx-runtime

const bridge = new RuntimeBridge();

// Example: Queue a dispatch
const event = await bridge.execCommand(
  {
    command: 'QueueDispatch',
    request_id: 'req-1',
    target: 'worker-1',
    body: { task_id: 'task-auth', description: 'Build auth handler' }
  },
  '.omx/state/team-auth-build'
);

// Returns:
// {
//   status: 'DispatchQueued',
//   dispatch_record: {
//     request_id: 'req-1',
//     target: 'worker-1',
//     status: 'pending',
//     created_at: '2026-06-19T14:00:00Z',
//     ...
//   }
// }

// Example: Mark dispatch delivered
const delivered = await bridge.execCommand(
  {
    command: 'MarkDelivered',
    request_id: 'req-1'
  },
  '.omx/state/team-auth-build'
);

// Command types:
type RuntimeCommand =
  | { command: 'AcquireAuthority', owner, lease_id, leased_until }
  | { command: 'RenewAuthority', owner, lease_id, leased_until }
  | { command: 'QueueDispatch', request_id, target, body }
  | { command: 'MarkNotified', request_id }
  | { command: 'MarkDelivered', request_id }
  | { command: 'MarkFailed', request_id }
  | { command: 'CreateMailboxMessage', from, to, body }
  | ...
```

---

## Auth Rotation

```typescript
// src/auth/rotation.ts

interface AuthSlotRecord {
  name: string;
  api_key: string;
  rate_limit_metadata: { remaining, reset_at };
  last_used_at: string;
}

// Rotation strategies:
type RotationMode = 'manual' | 'round-robin' | 'priority';

function buildRotationPlan(
  slots: AuthSlotRecord[],
  config: { mode: RotationMode, priority_order?: string[] }
): RotationOrder {
  // Returns ordered list of slot names to try
  // manual: [specified_slot]
  // round-robin: [slot1, slot2, slot3, ...]
  // priority: [primary, ...others]
}

// Before each Codex invocation:
const nextSlot = nextSlotAfter(
  rotationOrder,
  currentSlot,
  exhausted: ['slot1']  // Slots that hit quota
);

// Swap env var:
process.env.OPENAI_API_KEY = slots[nextSlot].api_key;

// Spawn Codex:
spawn('codex', [...args], { env: process.env });
```

---

## Hook Entry Points

```typescript
// src/hooks/keyword-detector.ts
// Parses skill keywords from user input

type SkillKeyword = 
  | '$ultragoal'
  | '$deep-interview'
  | '$ralplan'
  | '$team'
  | '$ralph'
  | '$code-review'
  | '$ask'
  | '$question';

// Example: User types "$ultragoal Build auth handler"
// Detector extracts: { skill: 'ultragoal', intent: 'Build auth handler' }

// src/hooks/agents-overlay.ts
// Generates AGENTS.md scoped to phase + mode

interface GeneratedOverlay {
  phase: AutopilotChildPhase;
  roles: AgentRoleDefinition[];
  instructions: string;
  context: string;
}

// Injected into Codex prompt:
// [AGENTS.md content]
// You are in phase: deep-interview
// Available agents: analyst, researcher, ...
// Instructions: Ask clarifying questions about...

// src/hooks/triage-heuristic.ts
// Estimates task complexity

function triageComplexity(prompt: string): 'simple' | 'moderate' | 'complex' {
  // Heuristics:
  // - Code file count
  // - Dependency depth
  // - Keyword matches ('refactor', 'debug', 'architect')
  // Returns: recommendation (direct, ultragoal, team)
}
```

---

## HUD Rendering Context

```typescript
// src/hud/state.ts

interface HudRenderContext {
  version: string;
  cwd: string;
  gitDisplay: { branch, ahead, behind };
  
  session: {
    phase: AutopilotRuntimePhase;
    activeWorkflows: string[];  // ['autopilot', 'mcp']
  };
  
  team?: {
    phase: TeamPhase | TerminalPhase;
    workerCount: number;
    taskSummary: { pending, claimed, inProgress, done };
    fixAttempt?: { current, max };
  };
  
  ralph?: {
    completionPercent: number;
    attemptNumber: number;
  };
  
  ultragoal?: {
    activeGoals: Array<{ id, title, status }>;
    completionPercent: number;
  };
  
  metrics: {
    timestamp: number;
    uptime: string;        // "1h 23m"
    notificationCount: number;
  };
}

// Presets:
type HudPreset = 'minimal' | 'focused' | 'full';

// Refresh interval: 1s (poll from .omx/state/ files)
```

---

## Team Claim Task API

```typescript
// Worker claims task from queue:
// $ omx team api claim-task --json

// Request:
{
  "worker_name": "executor-1",
  "timeout_seconds": 30
}

// Response:
{
  "claimed_task": {
    "id": "task-1",
    "description": "Build authentication handler",
    "owner": "executor-1",
    "status": "claimed",
    "claimed_at": "2026-06-19T14:00:00Z"
  }
}

// Worker marks done:
// $ omx team api mark-done --task-id=task-1 --json

// Response:
{
  "task_id": "task-1",
  "status": "done",
  "marked_at": "2026-06-19T14:15:00Z"
}
```

---

## File-Based Locking

```typescript
// src/team/state/locks.ts

// For concurrent file access in .omx/:
// 1. Use fs2 crate for POSIX file locks
// 2. Lock file: .omx/team/{team}/state/locks/{resource}.lock
// 3. Try to acquire exclusive lock
// 4. If blocked, retry with exponential backoff (max 5s)
// 5. Write state file once lock held
// 6. Release lock

// TS fallback:
import { lockFileSync } from 'proper-lockfile';

async function updateTaskState(taskId, newStatus) {
  const statePath = '.omx/state/team-xyz/tasks.json';
  const release = await lockFileSync(statePath, { retries: 10 });
  try {
    const tasks = JSON.parse(await readFile(statePath));
    tasks[taskId].status = newStatus;
    await writeFile(statePath, JSON.stringify(tasks));
  } finally {
    await release();
  }
}
```

---

## CLI Commands Reference

```bash
# Setup & initialization
omx setup                           # Initialize .omx/, hooks, AGENTS.md
omx doctor                          # Validate setup

# Direct execution
omx --direct                        # No tmux, plain CLI
omx --tmux                          # With HUD pane (default)

# Workflow entry points
$ultragoal "task description"       # Multi-goal execution
$deep-interview "refine scope"      # Clarification phase
$ralplan "review architecture"      # Plan approval
$team "split work across N agents"  # Multi-agent execution
$ralph "retry until success"        # Persistent loop

# Team operations
omx team 3:executor "task"          # Spawn 3 executor agents
omx team api claim-task             # Worker: claim task
omx team api mark-done --task-id=T  # Worker: mark task done

# State inspection
omx state list                      # List active sessions
omx state read [--scope=session-X]  # Read state
omx state write --json='{...}'      # Write state

# Cleanup
omx cleanup                         # Terminate sessions, clean .omx/

# Auth management
omx auth list                       # List credential slots
omx auth add --name=slot1 --key=... # Add credential
omx auth rotate                     # Test rotation strategy
```

---

## Environment Variables

```bash
# Launch behavior
export OMX_LAUNCH_POLICY=detached-tmux    # (direct, tmux, detached-tmux, auto)
export OMX_AUTO_UPDATE=defer              # (enabled, defer, disabled)
export OMX_RUNTIME_BRIDGE=1               # (1 = Rust, 0 = TS-direct fallback)

# Paths
export CODEX_HOME=~/.codex                # Codex config directory
export DISCORD_STATE_DIR=.discord-state   # Discord integration state

# Debug
export DEBUG=omx:*                        # Verbose logging
export OMX_COMPAT_TARGET=./target/debug/omx  # Use local Rust binary
```

---

## Key Type Definitions

```typescript
// src/autopilot/fsm.ts
export type AutopilotChildPhase = 
  | 'deep-interview'
  | 'ralplan'
  | 'ultragoal'
  | 'team'
  | 'ralph'
  | 'code-review'
  | 'ultraqa';

export type AutopilotRuntimePhase = AutopilotChildPhase | 'waiting-for-user' | 'complete' | 'failed';

// src/team/orchestrator.ts
export type TeamPhase = 'team-plan' | 'team-prd' | 'team-exec' | 'team-verify' | 'team-fix';
export type TerminalPhase = 'complete' | 'failed' | 'cancelled';

// src/team/state.ts
export interface TeamConfig {
  name: string;
  worker_count: number;
  tmux_session: string;
  lifecycle_profile: 'default' | 'aggressive' | 'conservative';
}

export interface WorkerInfo {
  name: string;
  index: number;
  role: string;           // e.g., 'executor', 'reviewer'
  assigned_tasks: string[];
  pane_id: string;        // tmux pane ID
  worktree: string;       // git worktree path
  status: 'idle' | 'working' | 'done';
}

export interface TeamTask {
  id: string;
  description: string;
  status: 'pending' | 'claimed' | 'in_progress' | 'done' | 'failed';
  owner?: string;         // worker name
  claimed_at?: string;
  completed_at?: string;
  error?: string;
}
```

---

## Plugin Hook Interface

```typescript
// User hook plugin: .omx/hooks/my-hook.mjs

export async function onHookEvent(event: HookEventEnvelope, sdk: HookPluginSdk) {
  const { eventType, payload } = event;
  
  switch (eventType) {
    case 'codex:before-model-call':
      // Inject context before Codex calls LLM
      return { ok: true, context: 'Additional context...' };
    
    case 'codex:after-completion':
      // Process Codex output
      const { output, phase } = payload;
      return { ok: true, processedOutput: output };
    
    case 'omx:phase-transition':
      // Track phase changes
      const { from, to } = payload;
      sdk.log(`Transitioned ${from} → ${to}`);
      return { ok: true };
    
    default:
      return { ok: false, error: 'Unknown event' };
  }
}

// sdk capabilities:
interface HookPluginSdk {
  cwd: string;
  sideEffectsEnabled: boolean;
  log(msg: string): void;
  readState(path: string): Promise<any>;
  writeState(path: string, data: any): Promise<void>;
}
```

---

## Skill Keywords

```typescript
// src/hooks/keyword-detector.ts

// User can type these keywords to trigger skill entry points:

$ultragoal "description"
  → Enter ultragoal mode, create multi-goal plan

$deep-interview "question"
  → Enter deep-interview phase, ask clarifying questions

$ralplan "what to build"
  → Request architecture review + approval

$team "task breakdown"
  → Spawn multi-agent team, split work across N workers

$ralph "task"
  → Persistent retry loop (attempt, check, retry if fail)

$code-review "what to review"
  → Code review pass, check for bugs + style

$ask "question"
  → Direct question to Codex (no workflow, just answer)

$question "prompt"
  → Interactive question (wait for answer, incorporate into context)
```

---

## Comparison: Direct vs Team Mode

```
DIRECT MODE (--direct)
┌─────────────────────────────────────┐
│ Main process                        │
│ ├─ Read task                        │
│ ├─ Spawn Codex                      │
│ ├─ Wait for completion              │
│ └─ Write state                      │
└─────────────────────────────────────┘

TEAM MODE (omx team N)
┌─────────────────────────────────────┐
│ Leader (main process)               │
│ ├─ Phase: team-plan → ... → done   │
│ ├─ Dispatch tasks                   │
│ └─ Monitor completion               │
└─────────────────────────────────────┘
    │       │       │
    ▼       ▼       ▼
┌────────┬────────┬──────────┐
│Worker1 │Worker2 │Worker3   │
│(pane 2)│(pane 3)│(pane 4)  │
│Claim   │Claim   │Claim     │
│Execute │Execute │Execute   │
│Mark    │Mark    │Mark      │
│Done    │Done    │Done      │
└────────┴────────┴──────────┘
```

---

## Authority Lease Cycle

```
1. Leader acquires lease (AcquireAuthority)
   - owner: "leader-1"
   - lease_id: "lease-abc123"
   - leased_until: 2026-06-19T14:30:00Z

2. Work happens (Codex executions)
   - Tasks dispatched, workers execute

3. Before lease expires, leader renews (RenewAuthority)
   - Extends leased_until to 2026-06-19T14:45:00Z

4. If leader crashes:
   - Another process waits until leased_until expires
   - Acquires authority, continues work
   - (Or can force-acquire with timeout check)
```

---

## Postinstall Flow

```bash
$ npm install -g oh-my-codex

# Postinstall hook runs:
→ node dist/scripts/postinstall.js

  1. Check if .omx/ already exists
     - If yes: skip setup, user can run `omx setup` manually
     - If no: prompt "Run setup now? (y/n)"

  2. If yes to setup:
     - Create .omx/ directory structure
     - Register hooks in .codex/config.toml
     - Generate initial AGENTS.md
     - Print success message

  3. If no / error:
     - Print "Run 'omx setup' later to initialize"
```

---

## Testing Entry Points

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:team:cross-rebase-smoke
npm run test:team:worker-runtime-identity
npm run test:recent-bug-regressions

# Run compat tests (Rust + TS interop)
npm run test:compat:rust

# Coverage for team-critical code
npm run coverage:team-critical
```

---

## Quick Debugging

```bash
# Check setup status
omx doctor

# Read current state
cat .omx/state/session-{id}/autopilot-state.json

# Read team state
cat .omx/state/team-{name}/team-state.json

# Read task queue
cat .omx/state/team-{name}/tasks.json

# Trace phase transitions
tail -f .omx/state/session-{id}/*.json

# Monitor HUD in real-time
omx hud --preset=full

# See Codex native hooks
cat .codex/config.toml | grep -A 10 "\[hooks\]"

# Check if omx-runtime is available
which omx-runtime  || echo "Not installed"

# Test auth rotation
omx auth rotate --dry-run
```

---

## Summary: When to Use Each Mode

| Use Case | Command | Why |
|----------|---------|-----|
| Quick one-off task | `omx --direct` | No overhead, instant |
| Long-running task | `omx --tmux` | HUD for progress visibility |
| Complex workflow | `$ultragoal "..."` | Multi-goal tracking + recovery |
| Parallel multi-agent | `omx team 3 "..."` | Split work, faster execution |
| Retry on failure | `$ralph "..."` | Built-in retry loop |
| Architecture review | `$ralplan "..."` | Approval gate before execution |
| Ad-hoc teams | `maw team "..."` | Quick multi-agent, no state |

