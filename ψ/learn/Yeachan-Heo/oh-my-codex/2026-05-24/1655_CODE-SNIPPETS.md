# oh-my-codex — Code Snippets & Architecture Flavor

**Repository**: Yeachan-Heo/oh-my-codex  
**Date**: 2026-05-24  
**Purpose**: Extract core patterns, key implementations, and architectural decisions

---

## Overview

**oh-my-codex (OMX)** is a **multi-agent orchestration layer** for OpenAI Codex CLI and other AI agents. It provides:
- 30+ specialized agent prompts as slash commands (`$deep-interview`, `$ralplan`, `$ultragoal`)
- 35+ workflow skills (SKILL.md files) for reusable task patterns
- AGENTS.md orchestration brain (project guidance + agent routing)
- 6 MCP servers for state, memory, code intelligence, tracing, wiki, and notifications
- Team runtime with tmux-backed parallel worker coordination
- Notification hooks (desktop, Discord, Telegram)

**Languages**: TypeScript/JavaScript + Rust (hybrid runtime)  
**Model**: Layered workflow engine (interview → planning → execution → verification)

---

## 1. Entry Point & Package Structure

### Main CLI Entry (ES modules)
**File**: `src/cli/omx.ts`

```typescript
#!/usr/bin/env node

import { fileURLToPath, pathToFileURL } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';
import { rememberOmxLaunchContext } from '../utils/paths.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const root = join(__dirname, '..', '..');

rememberOmxLaunchContext();

// Execute compiled entrypoint
const distEntry = join(root, 'dist', 'cli', 'index.js');

if (existsSync(distEntry)) {
  const { main } = await import(pathToFileURL(distEntry).href);
  await main(process.argv.slice(2));
  if (process.argv[2] !== 'mcp-serve') {
    process.exit(process.exitCode ?? 0);
  }
} else {
  console.error('oh-my-codex: run "npm run build" first');
  process.exit(1);
}
```

**Key pattern**: Imports compiled dist/, avoids in-repo requires, supports MCP server lifecycle (keeps process alive).

### Package.json Script Orchestration
**File**: `package.json`

```json
{
  "name": "oh-my-codex",
  "version": "0.18.2",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "omx": "dist/cli/omx.js"
  },
  "scripts": {
    "build": "node -e \"const fs=require('fs'); fs.rmSync('dist',{recursive:true,force:true});\" && tsc && node -e \"require('fs').chmodSync('dist/cli/omx.js', 0o755)\"",
    "build:full": "npm run build && npm run build:explore:release && npm run build:sparkshell && npm run build:api",
    "test": "npm run build && npm run verify:native-agents && npm run verify:plugin-bundle && npm run test:node && node dist/scripts/generate-catalog-docs.js --check"
  },
  "engines": {
    "node": ">=20"
  },
  "dependencies": {
    "@iarna/toml": "^2.2.5",
    "@modelcontextprotocol/sdk": "^1.26.0",
    "zod": "^4.3.6"
  }
}
```

**Flavor**: Multi-stage build (TypeScript → JS → plugin mirror sync → catalog docs generation). MCP SDK as core dependency, TOML parsing for Codex config.

---

## 2. Agent Model & Type System

### Agent Definitions — Role Routing Framework
**File**: `src/agents/definitions.ts`

```typescript
export interface AgentDefinition {
  name: string;
  description: string;
  reasoningEffort: 'low' | 'medium' | 'high';
  posture: 'frontier-orchestrator' | 'deep-worker' | 'fast-lane';
  modelClass: 'frontier' | 'standard' | 'fast';
  routingRole: 'leader' | 'specialist' | 'executor';
  tools: 'read-only' | 'analysis' | 'execution' | 'data';
  category: 'build' | 'review' | 'domain' | 'product' | 'coordination';
}

const EXECUTOR_AGENT: AgentDefinition = {
  name: 'executor',
  description: 'Code implementation, refactoring, feature work',
  reasoningEffort: 'medium',
  posture: 'deep-worker',
  modelClass: 'standard',
  routingRole: 'executor',
  tools: 'execution',
  category: 'build',
};

export const AGENT_DEFINITIONS: Record<string, AgentDefinition> = {
  'explore': {
    name: 'explore',
    description: 'Fast codebase search and file/symbol mapping',
    reasoningEffort: 'low',
    posture: 'fast-lane',
    modelClass: 'fast',
    routingRole: 'specialist',
    tools: 'read-only',
    category: 'build',
  },
  'architect': {
    name: 'architect',
    description: 'System design, boundaries, interfaces, long-horizon tradeoffs',
    reasoningEffort: 'high',
    posture: 'frontier-orchestrator',
    modelClass: 'frontier',
    routingRole: 'leader',
    tools: 'read-only',
    category: 'build',
  },
  // ... 20+ more agents (analyst, planner, debugger, verifier, style-reviewer, security-reviewer, etc.)
};
```

**Pattern**: Declarative agent schema decouples role routing from prompt content. Frontier vs standard vs fast model classes allow cost/latency optimization. Posture (orchestrator vs worker vs fast-lane) guides workflow insertion points.

---

## 3. Configuration & MCP Server Registry

### TOML Merger for Codex Config
**File**: `src/config/generator.ts` (excerpt)

```typescript
interface MergeOptions {
  includeTui?: boolean;
  codexHooksFile?: string;
  codexHomeDir?: string;
  hookCommandPlatform?: ManagedCodexHookOptions["platform"];
  codexHookFeatureFlag?: CodexHookFeatureFlag;
  modelOverride?: string;
  sharedMcpServers?: UnifiedMcpRegistryServer[];
  sharedMcpRegistrySource?: string;
  verbose?: boolean;
  statusLinePreset?: HudPreset;
  forceStatusLinePreset?: boolean;
  notifyCommand?: string[] | false;
  includeFirstPartyMcp?: boolean;
  preserveExistingFirstPartyMcp?: boolean;
}

export interface ModelContextRecommendation {
  model: string;
  modelContextWindow: number;
  modelAutoCompactTokenLimit: number;
}

export const DEFAULT_SETUP_MODEL = DEFAULT_FRONTIER_MODEL;
export const DEFAULT_SETUP_MODEL_CONTEXT_WINDOW = 250000;
export const DEFAULT_SETUP_MODEL_AUTO_COMPACT_TOKEN_LIMIT = 200000;

export function getModelContextRecommendation(
  model: string,
): ModelContextRecommendation | null {
  if (model !== DEFAULT_SETUP_MODEL) return null;

  return {
    model,
    modelContextWindow: DEFAULT_SETUP_MODEL_CONTEXT_WINDOW,
    modelAutoCompactTokenLimit: DEFAULT_SETUP_MODEL_AUTO_COMPACT_TOKEN_LIMIT,
  };
}

export const OMX_DEVELOPER_INSTRUCTIONS =
  "You have oh-my-codex installed. AGENTS.md is the orchestration brain and main control surface. Follow AGENTS.md for skill/keyword routing, $name workflow invocation, and role-specialized subagents. Use outcome-first, concise progress updates: state the target result, constraints, validation evidence, and stop condition before adding process detail.";
```

**Pattern**: Sealed model context recommendations (250K context window, 200K compact limit). Developer instructions baked as TOML prompt guidance, not runtime discovery. AGENTS.md is canonical orchestration surface.

---

## 4. MCP Server Routing & Dispatch

### MCP Serve Command — Server Entrypoint Router
**File**: `src/cli/mcp-serve.ts`

```typescript
type McpServeEntrypoint = (typeof OMX_FIRST_PARTY_MCP_ENTRYPOINTS)[number];

interface McpServeCommandOptions {
  env?: Record<string, string | undefined>;
  loaders?: McpServeLoaderMap;
  keepProcessAlive?: boolean;
}

const MCP_SERVE_LOADERS: McpServeLoaderMap = {
  "state-server.js": async () => await import("../mcp/state-server.js"),
  "memory-server.js": async () => await import("../mcp/memory-server.js"),
  "code-intel-server.js": async () => await import("../mcp/code-intel-server.js"),
  "trace-server.js": async () => await import("../mcp/trace-server.js"),
  "wiki-server.js": async () => await import("../mcp/wiki-server.js"),
  "hermes-server.js": async () => await import("../mcp/hermes-server.js"),
};

const MCP_SERVE_TARGET_ALIASES: Record<string, McpServeEntrypoint> = {
  state: "state-server.js",
  "state-server": "state-server.js",
  // ... aliases for all 6 servers
};

export function normalizeOmxMcpServeTarget(
  rawTarget: string | undefined,
): McpServeEntrypoint | null {
  if (typeof rawTarget !== "string") return null;
  const normalized = rawTarget.trim().toLowerCase();
  if (!normalized) return null;
  return MCP_SERVE_TARGET_ALIASES[normalized] ?? null;
}

export async function mcpServeCommand(
  args: string[],
  options: McpServeCommandOptions = {},
): Promise<void> {
  const target = normalizeOmxMcpServeTarget(args[0]);
  if (!target) {
    throw new Error(`Unknown MCP target: ${args[0]}`);
  }

  const env = options.env ?? process.env;
  const loaders = options.loaders ?? MCP_SERVE_LOADERS;
  env[MCP_ENTRYPOINT_MARKER_ENV] = target;
  
  await loaders[target]();
  if (options.keepProcessAlive === false) return;

  // MCP server modules start their stdio lifecycle as a side effect import.
  // Keep the process alive so stdio transport can communicate with Codex.
  await new Promise<never>(() => undefined);
}
```

**Pattern**: Lazy dynamic imports for MCP servers, kept alive by promise that never resolves. Plugins register via aliases. Each server is a separate stdio transport.

---

## 5. Notification System — Multi-Channel Delivery

### Notifier with Desktop, Discord, Telegram Support
**File**: `src/notifications/notifier.ts` (excerpt)

```typescript
export interface NotificationConfig {
  desktop?: boolean;
  discord?: {
    webhookUrl: string;
  };
  telegram?: {
    botToken: string;
    chatId: string;
  };
}

export interface NotificationPayload {
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  mode?: string;
  projectPath?: string;
}

export async function loadNotificationConfig(projectRoot?: string): Promise<NotificationConfig | null> {
  const configPath = join(projectRoot || process.cwd(), '.omx', 'notifications.json');
  if (!existsSync(configPath)) return null;
  try {
    return JSON.parse(await readFile(configPath, 'utf-8'));
  } catch {
    return null;
  }
}

export async function notify(payload: NotificationPayload, config?: NotificationConfig | null): Promise<void> {
  if (!config) {
    config = await loadNotificationConfig();
    if (!config) return;
  }

  const promises: Promise<void>[] = [];

  if (config.desktop) {
    promises.push(sendDesktopNotification(payload));
  }

  if (config.discord?.webhookUrl) {
    promises.push(sendDiscordNotification(payload, config.discord.webhookUrl));
  }

  if (config.telegram?.botToken && config.telegram?.chatId) {
    promises.push(sendTelegramNotification(payload, config.telegram.botToken, config.telegram.chatId));
  }

  await Promise.allSettled(promises);  // Fire and forget, no channel failure blocks others
}

export function _buildDesktopArgs(
  title: string,
  message: string,
  platform: string,
): [string, string[]] | null {
  if (platform === 'darwin') {
    // Escape backslashes then double-quotes for AppleScript string context
    const safeTitle = title.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    const safeMessage = message.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    return ['osascript', ['-e', `display notification "${safeMessage}" with title "${safeTitle}"`]];
  } else if (platform === 'linux') {
    return ['notify-send', [title, message]];
  } else if (platform === 'win32') {
    // Windows PowerShell toast
    // ...
  }
  return null;
}
```

**Pattern**: Pluggable notification backends loaded from `.omx/notifications.json`, platform-specific system calls (osascript for macOS, notify-send for Linux). Promise.allSettled prevents one channel from blocking others.

---

## 6. Team Runtime — Multi-Agent Orchestration

### Team Session & Worker Management
**File**: `src/team/tmux-session.ts` (excerpt)

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

const INJECTION_MARKER = '[OMX_TMUX_INJECT]';
const OMX_BYPASS_DEFAULT_SYSTEM_PROMPT_ENV = 'OMX_BYPASS_DEFAULT_SYSTEM_PROMPT';
const OMX_MODEL_INSTRUCTIONS_FILE_ENV = 'OMX_MODEL_INSTRUCTIONS_FILE';
const OMX_TEAM_WORKER_CLI_ENV = 'OMX_TEAM_WORKER_CLI';
const OMX_TEAM_WORKER_CLI_MAP_ENV = 'OMX_TEAM_WORKER_CLI_MAP';
const OMX_TEAM_WORKER_LAUNCH_MODE_ENV = 'OMX_TEAM_WORKER_LAUNCH_MODE';
const OMX_TEAM_AUTO_INTERRUPT_RETRY_ENV = 'OMX_TEAM_AUTO_INTERRUPT_RETRY';
const OMX_TEAM_WORKER_MCP_COMPAT_ENV = 'OMX_TEAM_WORKER_MCP_COMPAT';

const TEAM_WORKER_DISABLED_OMX_MCP_SERVERS = [
  'omx_state',
  'omx_memory',
  'omx_code_intel',
  'omx_trace',
  'omx_wiki',
  'omx_hermes',
] as const;

const TMUX_WORKER_AMBIENT_ENV_ALLOWLIST = [
  'HTTPS_PROXY',
  'HTTP_PROXY',
  'NO_PROXY',
  'https_proxy',
  'http_proxy',
  'no_proxy',
] as const;
```

**Pattern**: tmux session/window/pane structure as durable worker containers. Leader pane protected from cleanup. HUD pane managed separately with resize hooks. MCP servers selectively disabled for workers (state/memory/trace shared with leader only). Proxy env vars explicitly allowlisted (security isolation).

---

## 7. Keyword Detection & Workflow State

### Skill Activation & Keyword Routing
**File**: `src/hooks/keyword-detector.ts` (excerpt)

```typescript
export interface KeywordMatch {
  keyword: string;
  skill: string;
  priority: number;
}

const ACTIVE_SKILL_CONTINUATION_PATTERNS: RegExp[] = [
  /^[\\/]?\s*keep going(?:\s+now)?[.!]?\s*$/i,
  /^[\\/]?\s*continue(?:\s+now)?[.!]?\s*$/i,
  /^[\\/]?\s*resume(?:\s+now)?[.!]?\s*$/i,
];

export type SkillActivePhase = 'planning' | 'executing' | 'reviewing' | 'completing' | 'ralplan' | 'deep-interview';

export interface DeepInterviewInputLock {
  active: boolean;
  scope: 'deep-interview-auto-approval';
  acquired_at: string;
  released_at?: string;
  exit_reason?: 'success' | 'error' | 'abort' | 'handoff';
  blocked_inputs: string[];
  message: string;
}

export interface SkillActiveState {
  version: 1;
  active: boolean;
  skill: string;
  keyword: string;
  phase: string;
  activated_at: string;
  updated_at: string;
  source: 'keyword-detector';
  session_id?: string;
  thread_id?: string;
  turn_id?: string;
  input_lock?: DeepInterviewInputLock;
  active_skills?: SkillActiveEntry[];
}
```

**Pattern**: Workflow state machine tracks active skill + phase (planning/executing/reviewing). Input locks prevent shortcuts through deep-interview auto-approval. Continuation patterns allow "keep going" shorthand. State persisted to `.omx/` for recovery.

---

## 8. Rust Runtime Core — Event Log & Authority

### Dispatch & Authority System in Rust
**File**: `crates/omx-runtime-core/src/lib.rs` (excerpt)

```rust
pub const RUNTIME_SCHEMA_VERSION: u32 = 1;
pub const RUNTIME_COMMAND_NAMES: &[&str] = &[
    "acquire-authority",
    "renew-authority",
    "queue-dispatch",
    "mark-notified",
    "mark-delivered",
    "mark-failed",
    "request-replay",
    "capture-snapshot",
    "create-mailbox-message",
    "mark-mailbox-notified",
    "mark-mailbox-delivered",
];
pub const RUNTIME_EVENT_NAMES: &[&str] = &[
    "authority-acquired",
    "authority-renewed",
    "dispatch-queued",
    "dispatch-notified",
    "dispatch-delivered",
    "dispatch-failed",
    "replay-requested",
    "snapshot-captured",
    "mailbox-message-created",
    "mailbox-notified",
    "mailbox-delivered",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkerCli {
    Codex,
    Claude,
    Other(String),
}

impl WorkerCli {
    pub fn from_label(label: impl AsRef<str>) -> Self {
        match label.as_ref().trim().to_lowercase().as_str() {
            "claude" => Self::Claude,
            "codex" => Self::Codex,
            other => Self::Other(other.to_string()),
        }
    }
}

pub fn submit_presses_for_worker_cli(worker_cli: &WorkerCli) -> u8 {
    match worker_cli {
        WorkerCli::Claude => 1,
        WorkerCli::Codex | WorkerCli::Other(_) => 2,
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DispatchOutcomeReason {
    DeliveredConfirmed,
    DeliveredConfirmedActiveTask,
    DeliveredUnconfirmed,
    DeferredLeaderPaneMissing,
    DeferredShellNotInjectable,
    FailedMissingTarget,
    FailedTargetResolution(String),
    FailedPreflight(String),
    FailedSend(String),
}
```

**Pattern**: Event log schema separated into commands (mutable actions) and events (immutable records). Worker CLI type abstraction handles Claude vs Codex submission mechanics (different key counts). Dispatch outcome reasons provide durable failure classification.

---

## 9. Key Design Patterns & Idioms

### 1. **Sealed API via Config Seeding**
OMX bakes behavioral defaults into config.toml (model context, developer instructions) rather than runtime discovery. Prevents drift between setup time and execution.

### 2. **AGENTS.md as Canonical Orchestration Brain**
No global hardcoded prompt routing. Project guidance lives in repository's `AGENTS.md` (scoped Codex hook file). OMX reads it to make routing decisions.

### 3. **Keyword → Skill → Agent → CLI Routing**
Input detection (keyword-detector) → active workflow state (SkillActiveState) → agent selection (AGENT_DEFINITIONS) → prompt lookup (prompts/ directory) → Codex launch.

### 4. **Pluggable Backends via Dynamic Imports**
MCP servers, notification channels, team workers — all loaded dynamically via lazy `await import()`. Enables plugin discovery without coupling.

### 5. **Event Log for Durable Team State**
Rust-backed runtime log (authority acquire/renew, dispatch queued/notified/delivered) enables recovery and audit. Mailbox and task authority claims prevent race conditions.

### 6. **Promise.allSettled for Fault Tolerance**
Notifications, team dispatch, verification checks — all wrapped in `Promise.allSettled()` to prevent one channel/worker from blocking the whole workflow.

### 7. **Platform Command Abstraction**
`buildPlatformCommandSpec()` / `spawnPlatformCommandSync()` handle Darwin/Linux/Windows differences (osascript vs notify-send vs PowerShell). tmux pane detection guards against missing commands.

### 8. **Tmux Session Lifecycle Management**
Team session (session:window) → leader pane + N worker panes + HUD pane. Resize hooks, pane stability polls, process lifecycle tied to parent tmux session.

---

## 10. Configuration File Locations & Naming

- `.omx/` — Project root state directory (plans, logs, memory, sandboxes, team manifests)
- `.omx/notifications.json` — Notification config (channels, credentials)
- `.omx-config.json` — Model/env routing (optional per-project model override)
- `.codex/config.toml` — Codex CLI config (seeded by OMX with MCP servers, developer instructions)
- `.codex/hooks.json` — Lifecycle hooks (OMX-managed subset + user hooks)
- `AGENTS.md` — Orchestration brain (skills, keyword routing, role descriptions)
- `prompts/` — Agent prompt files (loaded by role router)
- `skills/` — SKILL.md files (workflow definitions)

---

## Summary: The OMX "Flavor"

**oh-my-codex is opinion-driven system design:**

1. **Workflow-first architecture**: Interview → Plan → Execute → Verify (durable multi-goal ledger)
2. **Sealed defaults**: Codex config seeded at setup time, not discovered at runtime
3. **Keyword-driven activation**: Input detection → skill state → agent dispatch (no hardcoded routes)
4. **Team runtime on tmux**: Parallel workers in isolated panes, leader-managed task authority
5. **MCP servers as peer systems**: State, memory, tracing, wiki — orthogonal to agent runtime
6. **Hybrid TypeScript/Rust**: TS for workflows & hooks, Rust for durable event log & authority
7. **Nothing is hardcoded**: Agents, skills, prompts, MCP servers all pluggable via AGENTS.md or dynamic imports
8. **Failure isolation**: Promise.allSettled for notifications, separate MCP transports for workers, retry loops for dispatch

**Core philosophy**: "Start Codex stronger, then let OMX add better prompts, workflows, and runtime help when the work grows."

