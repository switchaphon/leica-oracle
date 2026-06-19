# Oh-My-Codex (OMX) Code Snippets — Deep Dive 🐱

**Collected**: 2026-06-19  
**Source**: `/Users/switchaphon/ghq/github.com/Yeachan-Heo/oh-my-codex/src/`  
**Focus**: Codex spawn, resume, state, HUD, workers, plugins, CLI

---

## 1. Codex Launch & Spawn Mechanism

### `src/team/runtime.ts` — Core Orchestration

The runtime imports the core spawning infrastructure:

```typescript
import {
  sanitizeTeamName,
  isTmuxAvailable,
  hasCurrentTmuxClientContext,
  createTeamSession,
  buildWorkerProcessLaunchSpec,
  scrubTeamWorkerHudOwnershipEnv,
  resolveTeamWorkerCli,
  type TeamWorkerCli,
  resolveTeamWorkerCliPlan,
  resolveTeamWorkerLaunchMode,
  type TeamSession,
  waitForWorkerReady,
  waitForWorkerReadyAsync,
  dismissTrustPromptIfPresent,
  evaluateStartupDirectTriggerSafety,
  sendToWorker,
  sendToWorkerStdin,
  isWorkerAlive,
  isWorkerPaneOpen,
  getWorkerPanePid,
  killWorkerByPaneIdAsync,
  restoreStandaloneHudPane,
  teardownWorkerPanes,
  unregisterResizeHook,
  destroyTeamSession,
  listPaneIds,
  listTeamSessions,
  resolveSharedSessionShutdownTopology,
} from './tmux-session.js';
```

**Key insight**: The runtime delegates to `tmux-session.js` for all physical tmux operations. CLI spawn is abstracted through:
- `createTeamSession()` — Sets up tmux target
- `buildWorkerProcessLaunchSpec()` — Constructs spawn args
- `resolveTeamWorkerCli` — Chooses `codex` | `claude` | `gemini`

### `src/team/tmux-session.ts` — Spawn Implementation

The spawn mechanism is **header-driven**:

```typescript
export type TeamWorkerCli = 'codex' | 'claude' | 'gemini';
type TeamWorkerCliMode = 'auto' | TeamWorkerCli;
export type TeamWorkerLaunchMode = 'interactive' | 'prompt';

export interface WorkerProcessLaunchSpec {
  workerCli: TeamWorkerCli;
  command: string;
  args: string[];
  env: Record<string, string>;
}

interface WorkerLaunchSpec {
  shell: string;
  rcFile: string | null;
}
```

**Tmux constants**:

```typescript
const OMX_INSTANCE_OPTION = '@omx_instance_id';
const OMX_PANE_INSTANCE_OPTION = '@omx_pane_instance_id';

const TEAM_WORKER_DISABLED_OMX_MCP_SERVERS = [
  'omx_state',
  'omx_memory',
  'omx_code_intel',
  'omx_trace',
  'omx_wiki',
  'omx_hermes',
] as const;
```

**Session definition**:

```typescript
export interface TeamSession {
  name: string; // tmux target in "session:window" form
  workerCount: number;
  cwd: string;
  workerPaneIds: string[];
  /** Leader's own pane ID — must never be targeted by worker cleanup routines. */
  leaderPaneId: string;
  /** HUD pane spawned below the leader column, or null if creation failed. */
  hudPaneId: string | null;
  /** Registered tmux resize hook name for the HUD pane, or null if unavailable. */
  resizeHookName: string | null;
  /** Registered tmux resize hook target in "<session>:<window>" form, or null. */
  resizeHookTarget: string | null;
}
```

**Tmux helper**:

```typescript
function runTmux(args: string[]): { ok: true; stdout: string } | { ok: false; stderr: string } {
  const { result } = spawnPlatformCommandSync('tmux', args, { encoding: 'utf-8' });
  if (result.error) {
    return { ok: false, stderr: result.error.message };
  }
  if (result.status !== 0) {
    return { ok: false, stderr: (result.stderr || '').trim() || `tmux exited ${result.status}` };
  }
  return { ok: true, stdout: (result.stdout || '').trim() };
}
```

---

## 2. Resume Mechanism & Worker Lifecycle

The resume mechanism is embedded in the **WorkerSubmitPlan**:

```typescript
export interface WorkerSubmitPlan {
  shouldInterrupt: boolean;
  queueFirstRound: boolean;
  rounds: number;
  submitKeyPressesPerRound: number;
  allowAdaptiveRetry: boolean;
}
```

**Note**: There is no separate `src/cli/resume.ts` file. Resume state is managed through:
1. **Task state in `src/state/operations.ts`** — persisted lifecycle
2. **Worker heartbeat** — liveness check
3. **Inbox/mailbox flow** — async steering

---

## 3. State Management — Deep Persistence

### `src/state/operations.ts` — State Ops & Autopilot

**Atomic file write helper** (at-rest consistency):

```typescript
async function writeAtomicFile(path: string, data: string): Promise<void> {
  const tmpPath = `${path}.tmp.${process.pid}.${Date.now()}.${Math.random().toString(16).slice(2)}`;
  await writeFile(tmpPath, data, 'utf-8');
  try {
    await rename(tmpPath, path);
  } catch (error) {
    await unlink(tmpPath).catch(() => {});
    throw error;
  }
}
```

**Write lock for concurrent state mutations**:

```typescript
const stateWriteQueues = new Map<string, Promise<void>>();

async function withStateWriteLock<T>(path: string, fn: () => Promise<T>): Promise<T> {
  const tail = stateWriteQueues.get(path) ?? Promise.resolve();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const queued = tail.finally(() => gate);
  stateWriteQueues.set(path, queued);

  await tail.catch(() => {});
  try {
    return await fn();
  } finally {
    release();
    if (stateWriteQueues.get(path) === queued) {
      stateWriteQueues.delete(path);
    }
  }
}
```

**Autopilot FSM phase order** (deterministic state machine):

```typescript
const AUTOPILOT_CHILD_PHASE_ORDER: AutopilotChildPhase[] = [
  'deep-interview',
  'ralplan',
  'ultragoal',
  'team',
  'ralph',
  'code-review',
  'ultraqa',
];

function autopilotPhaseOrder(phase: AutopilotChildPhase | null): number {
  return phase ? AUTOPILOT_CHILD_PHASE_ORDER.indexOf(phase) : -1;
}

function isForwardAutopilotPhase(
  currentPhase: AutopilotChildPhase | null,
  nextPhase: AutopilotChildPhase | null,
): boolean {
  const currentOrder = autopilotPhaseOrder(currentPhase);
  const nextOrder = autopilotPhaseOrder(nextPhase);
  return currentOrder >= 0 && nextOrder > currentOrder;
}

function isNextAutopilotPhase(
  currentPhase: AutopilotChildPhase | null,
  nextPhase: AutopilotChildPhase | null,
): boolean {
  const currentOrder = autopilotPhaseOrder(currentPhase);
  const nextOrder = autopilotPhaseOrder(nextPhase);
  return currentOrder >= 0 && nextOrder === currentOrder + 1;
}
```

**Supported state modes**:

```typescript
export const SUPPORTED_STATE_READ_MODES = [
  'autopilot',
  'autoresearch',
  'team',
  'ralph',
  'ultrawork',
  'ultraqa',
  'ralplan',
  'deep-interview',
  'skill-active',
] as const;

export type StateOperationName =
  | 'state_read'
  | 'state_write'
  | 'state_clear'
  | 'state_list_active'
  | 'state_get_status';
```

---

## 4. HUD Reconcile Loop

### `src/hud/reconcile.ts` — Pane Lifecycle

**HUD owner environment flag**:

```typescript
export const OMX_TMUX_HUD_OWNER_ENV = 'OMX_TMUX_HUD_OWNER';

function isExplicitOmxOwnedTmuxEnv(env: NodeJS.ProcessEnv): boolean {
  return env[OMX_TMUX_HUD_OWNER_ENV] === '1';
}
```

**Orphan HUD reaper** (cleanup dead leader references):

```typescript
/**
 * Kill HUD watch panes that belong to the *current* session but whose owning
 * leader pane is no longer alive in this window.
 *
 * When a leader pane is destroyed (e.g. during a `team` setup/teardown cycle that
 * tears down the leader REPL pane), its owner-tagged HUD panes are left pointing at
 * the dead leader id. They are matched by neither `findHudWatchPaneIds` — whose
 * owner check requires the recorded leader to equal the current pane — nor
 * `findLegacyFocusedHudWatchPaneIds`, which only adopts HUD panes that *lack* owner
 * metadata. So the reconcile below sees "no HUD", recreates one, and repeats on
 * every prompt submit until the window degenerates into a column of stacked HUD
 * strips with no leader or worker panes left.
 *
 * The reap is intentionally scoped to the current session: HUD panes owned by other
 * sessions (whose leader may legitimately live in a different tmux window we cannot
 * see from this window's pane list) are never touched.
 */
function reapOrphanedSessionHudPanes(
  panes: TmuxPaneSnapshot[],
  opts: {
    sessionId: string | undefined;
    sessionIds?: string[];
    currentPaneId: string | undefined;
    killPane: (paneId: string) => boolean;
  },
): string[] {
  const { sessionId, currentPaneId, killPane } = opts;
  const sameSessionIds = new Set(
    [sessionId, ...(opts.sessionIds ?? [])]
      .map((candidate) => candidate?.trim() ?? '')
      .filter((candidate) => candidate !== ''),
  );
  if (sameSessionIds.size === 0) return [];
  // A recorded leader only counts as "live" if it exists in this window AND is not
  // itself a HUD watcher.
  const liveNonHudPaneIds = new Set(
    panes.filter((pane) => !isHudWatchPane(pane)).map((pane) => pane.paneId),
  );
  const reaped: string[] = [];
  for (const pane of panes) {
    if (!isHudWatchPane(pane)) continue;
    const owner = readHudPaneOwner(pane);
    // Only reclaim HUDs that explicitly belong to this session and name a leader.
    if (!owner.sessionId || !sameSessionIds.has(owner.sessionId) || !owner.leaderPaneId) continue;
    // Keep HUDs whose leader is the current pane or another live non-HUD leader pane.
    if (owner.leaderPaneId === currentPaneId || liveNonHudPaneIds.has(owner.leaderPaneId)) continue;
    if (killPane(pane.paneId)) reaped.push(pane.paneId);
  }
  return reaped;
}

function hasExplicitHudOwnerMarker(pane: TmuxPaneSnapshot): boolean {
  const command = `${pane.startCommand} ${pane.currentCommand}`;
  return new RegExp(`(?:^|\\s)${OMX_TMUX_HUD_OWNER_ENV}=(?:'1'|1)(?=$|\\s)`).test(command);
}
```

**HUD reconcile result**:

```typescript
export interface ReconcileHudForPromptSubmitResult {
  status:
    | 'skipped_not_tmux'
    | 'skipped_no_entry'
    | 'skipped_not_omx_owned_tmux'
    | 'skipped_no_session_id'
    | 'skipped_window_too_cramped'
    | 'unchanged'
    | 'resized'
    | 'recreated'
    | 'replaced_duplicates'
    | 'failed';
  paneId: string | null;
  desiredHeight: number | null;
  duplicateCount: number;
}
```

---

## 5. Worker Bootstrap — Instructions & Setup

### `src/team/worker-bootstrap.ts` — Inline Runtime Instructions

**Generated worker instructions file**:

```typescript
export function generateWorkerRootAgentsContent(
  options: WorkerRootAgentsOptions,
): string {
  return `# Team Worker Runtime Instructions

This file is generated for a live OMX team worker run and is disposable.

## Worker Identity
- Team: ${options.teamName}
- Worker: ${options.workerName}
- Role: ${options.workerRole}
- Leader cwd: ${options.leaderCwd}
- Worktree root: ${options.worktreePath}
- Team state root: ${options.teamStateRoot}
- Inbox path: ${options.teamStateRoot}/team/${options.teamName}/workers/${options.workerName}/inbox.md
- Mailbox path: ${options.teamStateRoot}/team/${options.teamName}/mailbox/${options.workerName}.json
- Leader mailbox path: ${options.teamStateRoot}/team/${options.teamName}/mailbox/leader-fixed.json
- Task directory: ${options.teamStateRoot}/team/${options.teamName}/tasks
- Worker status path: ${options.teamStateRoot}/team/${options.teamName}/workers/${options.workerName}/status.json
- Worker identity path: ${options.teamStateRoot}/team/${options.teamName}/workers/${options.workerName}/identity.json

## Protocol
1. Read your inbox at \`${options.teamStateRoot}/team/${options.teamName}/workers/${options.workerName}/inbox.md\`.
2. Load the worker skill from the first existing path:
   - \`${"${CODEX_HOME:-~/.codex}"}/skills/worker/SKILL.md\`
   - \`${options.leaderCwd}/.codex/skills/worker/SKILL.md\`
   - \`${options.leaderCwd}/skills/worker/SKILL.md\`
3. Send startup ACK before task work:

   \`omx team api send-message --input "{\"team_name\":\"${options.teamName}\",\"from_worker\":\"${options.workerName}\",\"to_worker\":\"leader-fixed\",\"body\":\"ACK: ${options.workerName} initialized\"}" --json\`

4. Resolve canonical team state root in this order: \`OMX_TEAM_STATE_ROOT\` env -> worker identity \`team_state_root\` -> config/manifest \`team_state_root\` -> local cwd fallback.
5. Read task files from \`${options.teamStateRoot}/team/${options.teamName}/tasks/task-<id>.json\` using bare \`task_id\` values in APIs.
6. Use claim-safe lifecycle APIs only:
   - \`omx team api claim-task --json\`
   - \`omx team api transition-task-status --json\`
   - \`omx team api release-task-claim --json\` only for rollback to pending
7. Use mailbox delivery flow:
   - \`omx team api mailbox-list --input "{\"team_name\":\"${options.teamName}\",\"worker\":\"${options.workerName}\"}" --json\`
   - \`omx team api mailbox-mark-delivered --input "{\"team_name\":\"${options.teamName}\",\"worker\":\"${options.workerName}\",\"message_id\":\"<MESSAGE_ID>\"}" --json\`
8. Preserve leader steering via inbox/mailbox nudges; task payload stays in inbox/task JSON, not this file.
9. Do not pass \`workingDirectory\` to legacy team_* MCP tools; use \`omx team api\` CLI interop.

## Message Protocol
- Always include \`from_worker: "${options.workerName}"\`
- Send leader messages to \`to_worker: "leader-fixed"\`

## Team Coordination Gate
- Keep independent fan-out lightweight: normal ACK, claim-safe lifecycle, status, and verification are enough.
- For dependencies, shared files/surfaces, handoffs, integration, blocked lanes, or changed assumptions, activate the Team Big Five / ATEM-inspired protocol: shared mental model/source of truth, ACK-readback handoffs, boundary monitoring, backup/reassignment requests, adaptability checkpoints, and team-outcome orientation.

## Scope Rules
- Follow task-specific edit scope from inbox/task JSON only.
- If blocked on a shared file, update status with a blocked reason and report upward.

<!-- OMX:TEAM:ROLE:START -->
<team_worker_role>
You are operating as the **${options.workerRole}** role for this team run. Apply the following role-local guidance.

${options.rolePromptContent.trim()}
</team_worker_role>
<!-- OMX:TEAM:ROLE:END -->
\`;
}
```

**Worker identity options**:

```typescript
interface WorkerRootAgentsOptions {
  teamName: string;
  workerName: string;
  workerRole: string;
  rolePromptContent: string;
  teamStateRoot: string;
  leaderCwd: string;
  worktreePath: string;
}

interface WorkerRootAgentsBackup {
  existed: boolean;
  tracked: boolean;
  previousContent?: string;
  skipWorktreeApplied?: boolean;
}
```

**Git exclude pattern injection** (keep generated files out of version control):

```typescript
async function ensureGitInfoExcludePattern(
  worktreePath: string,
  pattern: string,
): Promise<void> {
  const excludePath = tryReadGitValue(worktreePath, [
    "rev-parse",
    "--git-path",
    "info/exclude",
  ]);
  if (!excludePath) return;
  const existing = existsSync(excludePath)
    ? await readFile(excludePath, "utf-8")
    : "";
  const lines = new Set(existing.split(/\r?\n/).filter(Boolean));
  if (lines.has(pattern)) return;
  const next = `${existing}${existing.endsWith("\n") || existing.length === 0 ? "" : "\n"}${pattern}\n`;
  await mkdir(dirname(excludePath), { recursive: true });
  await writeFile(excludePath, next, "utf-8");
}
```

---

## 6. Plugin Runner — Hook Extensibility

### `src/hooks/extensibility/plugin-runner.ts` — Subprocess Harness

**Plugin result encoding** (IPC via stdout):

```typescript
interface RunnerRequest {
  cwd: string;
  pluginId?: string;
  pluginPath: string;
  event: HookEventEnvelope;
  sideEffectsEnabled?: boolean;
}

interface RunnerResult {
  ok: boolean;
  plugin: string;
  reason: string;
  error?: string;
}

const RESULT_PREFIX = '__OMX_PLUGIN_RESULT__ ';

function emitResult(result: RunnerResult): void {
  writeSync(process.stdout.fd, `${RESULT_PREFIX}${JSON.stringify(result)}\n`);
}

function finish(result: RunnerResult, exitCode: number): void {
  process.exitCode = exitCode;
  emitResult(result);
  process.exit(exitCode);
}
```

**Plugin loading & execution**:

```typescript
async function main(): Promise<void> {
  const raw = await readStdin();
  if (!raw) {
    finish({ ok: false, plugin: 'unknown', reason: 'empty_request' }, 1);
    return;
  }

  let request: RunnerRequest;
  try {
    request = JSON.parse(raw) as RunnerRequest;
  } catch {
    finish({ ok: false, plugin: 'unknown', reason: 'invalid_json' }, 1);
    return;
  }

  const pluginId = (request.pluginId || basename(request.pluginPath || 'unknown')).trim() || 'unknown';

  try {
    const moduleUrl = `${pathToFileURL(request.pluginPath).href}?t=${Date.now()}`;
    const loaded = await import(moduleUrl) as HookPluginModule;
    if (typeof loaded.onHookEvent !== 'function') {
      finish({ ok: false, plugin: pluginId, reason: 'invalid_export' }, 1);
      return;
    }

    const sdk = createHookPluginSdk({
      cwd: request.cwd,
      pluginName: pluginId,
      event: request.event,
      sideEffectsEnabled: request.sideEffectsEnabled !== false,
    });

    await Promise.resolve(loaded.onHookEvent(request.event, sdk));
    finish({ ok: true, plugin: pluginId, reason: 'ok' }, 0);
  } catch (error) {
    finish({
      ok: false,
      plugin: pluginId,
      reason: 'runner_error',
      error: error instanceof Error ? error.message : String(error),
    }, 1);
  }
}

await main().catch((error) => {
  finish({
    ok: false,
    plugin: 'unknown',
    reason: 'runner_error',
    error: error instanceof Error ? error.message : String(error),
  }, 1);
});
```

**Key pattern**: Plugins are loaded dynamically with cache-bust (`?t=${Date.now()}`), executed in subprocess, and results emit via `__OMX_PLUGIN_RESULT__` prefix on stdout.

---

## 7. CLI Entry Point

### `src/cli/index.ts` — Command Router

**Command imports**:

```typescript
import { setup, SETUP_MCP_MODES, SETUP_SCOPES, SETUP_TEAM_MODES } from "./setup.js";
import { uninstall } from "./uninstall.js";
import { version } from "./version.js";
import { tmuxHookCommand } from "./tmux-hook.js";
import { hooksCommand } from "./hooks.js";
import { hudCommand } from "../hud/index.js";
import { sidecarCommand } from "../sidecar/index.js";
import { teamCommand } from "./team.js";
import { ralphCommand } from "./ralph.js";
import { ultragoalCommand } from "./ultragoal.js";
import { performanceGoalCommand } from "./performance-goal.js";
import { askCommand } from "./ask.js";
import { questionCommand } from "./question.js";
import { stateCommand } from "./state.js";
import { cleanupCommand, cleanupOmxMcpProcesses } from "./cleanup.js";
import { exploreCommand } from "./explore.js";
import { sparkshellCommand } from "./sparkshell.js";
import { apiCommand } from "./api.js";
import { agentsInitCommand } from "./agents-init.js";
import { agentsCommand } from "./agents.js";
import { sessionCommand } from "./session-search.js";
import { autoresearchCommand } from "./autoresearch.js";
import { autoresearchGoalCommand } from "./autoresearch-goal.js";
import { mcpParityCommand } from "./mcp-parity.js";
import { mcpServeCommand } from "./mcp-serve.js";
import { adaptCommand } from "./adapt.js";
import { listCommand } from "./list.js";
import { authCommand } from "./auth.js";
```

**CLI flags** (constants):

```typescript
export {
  MADMAX_FLAG,
  CODEX_BYPASS_FLAG,
  HIGH_REASONING_FLAG,
  XHIGH_REASONING_FLAG,
  SPARK_FLAG,
  MADMAX_SPARK_FLAG,
  CONFIG_FLAG,
  LONG_CONFIG_FLAG,
} from "./constants.js";
```

**Key utilities exported**:

```typescript
export function resolveNotifyFallbackWatcherScript(pkgRoot = getPackageRoot()): string {
  return resolveDistScript(pkgRoot, "notify-fallback-watcher.js");
}

export function resolveHookDerivedWatcherScript(pkgRoot = getPackageRoot()): string {
  return resolveDistScript(pkgRoot, "hook-derived-watcher.js");
}

export function resolveNotifyHookScript(pkgRoot = getPackageRoot()): string {
  return resolveDistScript(pkgRoot, "notify-hook.js");
}

function resolveDistScript(pkgRoot: string, scriptName: string): string {
  return join(pkgRoot, "dist", "scripts", scriptName);
}
```

**Context memory** (session tracking):

```typescript
rememberOmxLaunchContext({ argv1: process.argv[1], cwd: process.cwd(), env: process.env });
```

---

## 8. Setup & Install

### `src/cli/setup.ts` — Installation Orchestration

**Setup types**:

```typescript
import {
  SETUP_INSTALL_MODES,
  SETUP_MCP_MODES,
  SETUP_SCOPES,
  getSetupScopeFilePath,
  readPersistedSetupPreferences,
  type PersistedSetupScope,
  type SetupInstallMode,
  type SetupMcpMode,
  type SetupScope,
} from "./setup-preferences.js";
```

**Setup modes & targets**:

```typescript
type PluginDeveloperInstructionsDecisionAction = "add" | "update" | "preserve";
```

**HUD config resolution**:

```typescript
async function resolveStatusLinePresetForSetup(
  projectRoot: string,
  options: Pick<SetupOptions, "force">,
): Promise<HudPreset | undefined> {
  if (options.force) {
    return DEFAULT_HUD_CONFIG.statusLine.preset;
  }
  const path = join(projectRoot, ".omx", "hud-config.json");
  if (!existsSync(path)) return undefined;
  try {
    const raw = JSON.parse(await readFile(path, "utf-8")) as {
      statusLine?: { preset?: unknown };
    };
    const preset = raw?.statusLine?.preset;
    if (preset === "minimal" || preset === "focused" || preset === "full") {
      return preset;
    }
  } catch {
    // Malformed hud-config.json — fall through to default.
  }
  return undefined;
}
```

**Setup scope target** (user-local, project, workspace):

```typescript
import { readPersistedSetupPreferences, resolveCodexConfigPathForLaunch } from "./codex-home.js";
```

---

## Key Architecture Patterns 🔍

### 1. **Atomic State Writes**
- Temp file → rename (POSIX atomicity)
- Write lock queue per path
- Prevents concurrent corruption

### 2. **Process Isolation**
- Workers = subprocess spawned via tmux
- Plugin runner = subprocess with stdin/stdout
- All communication async (files + mailbox)

### 3. **Ownership Tracking**
- HUD panes tagged with `OMX_TMUX_HUD_OWNER_ENV`
- Leader ID + session ID prevents cross-session contamination
- Orphan reaper cleans dead references

### 4. **State Machine**
- Autopilot = strict FSM with ordered phases
- No backward transitions allowed
- Deterministic phase order

### 5. **Declarative Instructions**
- Worker receives `AGENTS.md` + inbox JSON
- No imperative commands; state is the instruction
- Scope rules embedded in task payload

### 6. **Claim-Safe Lifecycle**
- `claim-task` → exclusive work
- `transition-task-status` → atomic update
- `release-task-claim` → rollback only

---

## Environment Variables Used

| Variable | Purpose | Source |
|----------|---------|--------|
| `OMX_TMUX_HUD_OWNER` | HUD pane ownership marker | `hud/reconcile.ts` |
| `OMX_TMUX_HUD_LEADER_PANE` | Leader pane ID for HUD binding | `hud/tmux.js` |
| `OMX_TEAM_STATE_ROOT` | Canonical state directory | `team/tmux-session.ts` |
| `OMX_TEAM_WORKER_CLI` | Which CLI to spawn (`codex\|claude\|gemini`) | `team/tmux-session.ts` |
| `OMX_LEADER_NODE_PATH` | Node.js binary for leader process | `team/tmux-session.ts` |
| `OMX_BYPASS_DEFAULT_SYSTEM_PROMPT` | Skip default system prompt injection | `team/tmux-session.ts` |

---

**End of Code Snippets Document**  
Generated by: Leica 🐱  
Date: 2026-06-19 13:39 UTC
