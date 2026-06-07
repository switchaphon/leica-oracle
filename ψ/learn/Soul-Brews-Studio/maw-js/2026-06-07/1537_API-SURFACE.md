# maw-js — Public API Surface & Integration Guide

**Source**: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/maw-js`  
**Version**: v26.6.8-alpha.1320 (CalVer)  
**License**: BUSL-1.1  
**Documentation Date**: 2026-06-07

---

## Table of Contents

1. [Package Exports](#package-exports)
2. [SDK API Surface](#sdk-api-surface)
3. [Plugin System](#plugin-system)
4. [HTTP Server & API Endpoints](#http-server--api-endpoints)
5. [Federation Protocol](#federation-protocol)
6. [Channel System](#channel-system)
7. [Extension Points & Hooks](#extension-points--hooks)
8. [Transport Layer](#transport-layer)
9. [Creating a Plugin](#creating-a-plugin)
10. [Creating a Command](#creating-a-command)

---

## Package Exports

### Canonical exports via `package.json`

```json
{
  "exports": {
    ".": "./src/cli.ts",
    "./sdk": "./src/sdk/index.ts",
    "./config": "./src/config.ts",
    "./config/ghq-root": "./src/config/ghq-root.ts",
    "./config/types": "./src/config/types.ts",
    "./schemas": "./src/lib/schemas.ts",
    "./cli/parse-args": "./src/cli/parse-args.ts",
    "./plugin/types": "./src/plugin/types.ts",
    "./plugin/manifest": "./src/plugin/manifest.ts",
    "./plugin/lifecycle": "./src/plugin/lifecycle.ts",
    "./plugin/registry": "./src/plugin/registry.ts",
    "./core/consent": "./src/core/consent/index.ts",
    "./core/fleet/audit": "./src/core/fleet/audit.ts",
    "./core/fleet/leaf": "./src/core/fleet/leaf.ts",
    "./core/fleet/nicknames": "./src/core/fleet/nicknames.ts",
    "./core/fleet/validate": "./src/core/fleet/validate.ts",
    "./core/fleet/worktree-layout": "./src/core/fleet/worktree-layout.ts",
    "./core/ghq": "./src/core/ghq.ts",
    "./core/resolve": "./src/core/resolve.ts",
    "./core/transport/ssh": "./src/core/transport/ssh.ts",
    "./core/transport/tmux": "./src/core/transport/tmux.ts",
    "./lib/artifacts": "./src/lib/artifacts.ts",
    "./lib/feed": "./src/lib/feed.ts",
    "./commands/shared/comm": "./src/commands/shared/comm.ts",
    "./commands/shared/federation": "./src/commands/shared/federation.ts"
  }
}
```

**Key entry points**:
- `maw-js` (default) — CLI binary
- `maw-js/sdk` — Main SDK for plugins; re-exports stable types & utilities
- `maw-js/plugin/types` — `InvokeContext`, `InvokeResult`, `PluginManifest`, `LoadedPlugin`
- `maw-js/core/transport/tmux` — Tmux session/window/pane control
- `maw-js/lib/artifacts` — Artifact storage and retrieval

---

## SDK API Surface

Located: `src/sdk/index.ts`  
Package: `@maw-js/sdk` (for external consumers)

### Core Types

#### `InvokeContext`
Plugin invocation input — passed by the host to every plugin handler.

```typescript
interface InvokeContext {
  source: "cli" | "api" | "peer";
  args: string[] | Record<string, unknown>;
  matchedName?: string;           // Alias-aware plugins use this for deprecation warnings
  writer?: (...args: unknown[]) => void;  // Output writer (CLI → stdout, API → undefined)
  flags?: Record<string, boolean | string | number | string[]>;  // Parsed CLI flags
}
```

#### `InvokeResult`
Plugin invocation output — returned by handler.

```typescript
interface InvokeResult {
  ok: boolean;
  output?: string;                // Response body
  error?: string;                 // Error message (when ok: false)
  exitCode?: number;              // Optional exit code (default 1 on failure)
}
```

#### `PluginManifest`
Metadata that describes a plugin. Loaded from `plugin.json` inside the plugin package.

```typescript
interface PluginManifest {
  name: string;                              // Unique slug /^[a-z0-9-]+$/
  version: string;                           // Semver
  weight?: number;                           // Execution order (default 50)
  tier?: "core" | "standard" | "extra";      // Membership contract
  wasm?: string;                             // Path to .wasm (WASM plugin)
  entry?: string;                            // Path to .ts/.js (TS plugin)
  sdk: string;                               // SDK version range "^1.0.0"
  target?: "js" | "wasm";                    // Compile target (Phase A: "js" only)
  capabilities?: string[];                   // "namespace:verb" (advisory Phase A)
  capabilityNamespaces?: string[];           // Plugin-owned capability namespaces
  dependencies?: { plugins?: string[] };     // Plugins this needs before dispatch
  artifact?: { path: string; sha256: string | null }; // Built bundle metadata
  cli?: {
    command: string;
    aliases?: string[];
    help?: string;
    flags?: Record<string, "boolean" | "string" | "number">;
  };
  api?: { path: string; methods: ("GET" | "POST")[] };
  description?: string;
  author?: string;
  hooks?: {
    gate?: string[];              // Event names to gate
    filter?: string[];            // Event names to filter
    on?: string[];                // Event names to handle
    late?: string[];              // Event names for cleanup
    wake?: PluginLifecycleHook;   // Oracle/session wake
    sleep?: PluginLifecycleHook;  // Oracle/session sleep
    serve?: PluginLifecycleHook;  // Persistent process serve
  };
  cron?: {
    schedule: string;             // Cron expression
    handler?: string;             // Export name (default "onTick")
  };
  module?: {
    exports: string[];            // Named exports for other plugins
    path: string;                 // Relative path to module
  };
  transport?: { peer?: boolean }; // Enable "maw hey plugin:<name>"
  engine?: {
    serve?: PluginEngineServe;    // Persistent process metadata
  };
}
```

#### `LoadedPlugin`
Runtime representation of a loaded & validated plugin.

```typescript
interface LoadedPlugin {
  manifest: PluginManifest;
  dir: string;                    // Absolute path to plugin directory
  wasmPath: string;               // Resolved path to .wasm
  entryPath?: string;             // Resolved path to .ts/.js (TS plugins only)
  kind: "wasm" | "ts";
  disabled?: boolean;
}
```

### Plugin Definition Helpers

#### `definePlugin(config: PluginConfig): PluginConfig`

Type-safe plugin definition. Like Vue's `defineComponent()` — validates shape, zero runtime overhead.

```typescript
interface PluginConfig {
  name: string;
  handler: (ctx: InvokeContext) => Promise<InvokeResult>;
  onGate?: (event: any) => boolean;           // Phase 0: GATE
  onFilter?: (event: any) => any;             // Phase 1: FILTER
  onEvent?: (event: any) => void | Promise<void>;  // Phase 2: HANDLE
  onLate?: (event: any) => void;              // Phase 3: LATE
  onInstall?: () => void | Promise<void>;
  onUninstall?: () => void | Promise<void>;
}
```

### Configuration

```typescript
loadConfig(): MawConfig
saveConfig(config: MawConfig): void
buildCommand(cmd: string): string
buildCommandInDir(dir: string, cmd: string): string
getEnvVars(): Record<string, string>
cfgTimeout(): number
cfgLimit(key: string): number
cfgInterval(key: string): number
cfg(key: string): any
resetConfig(): void

// Paths
getGhqRoot(): string
isMawXdgEnabled(): boolean
mawCacheDir(): string
mawConfigDir(): string
mawDataDir(): string
mawDataPath(...segments: string[]): string
mawMessageLogPath(): string
mawStateDir(): string
mawStatePath(...segments: string[]): string

// Engines
DEFAULT_ENGINES: EngineDef[]
resolveEngine(id: string): EngineDef
```

### Consent Management

```typescript
listPending(): ConsentAction[]
listTrust(): string[]
recordTrust(fingerprint: string): void
removeTrust(fingerprint: string): void
approveConsent(fingerprint: string): void
rejectConsent(fingerprint: string): void
```

### Transport Layer

#### Tmux Control

```typescript
tmux: Tmux                        // Global instance
Tmux(socketPath?: string)         // Constructor
tmuxCmd(cmd: string[]): string[]  // Build tmux command

// Session/window/pane management
withPaneLock(target: string, fn: () => Promise<T>): Promise<T>
splitWindowLocked(opts: SplitWindowLockedOpts): Promise<{ pane: string }>
tagPane(opts: TagPaneOpts): void
readPaneTags(target: string): PaneTags

// Types
interface TmuxPane { id: string; title: string; command?: string }
interface TmuxWindow { id: string; name: string; panes: TmuxPane[] }
interface TmuxSession { name: string; windows: TmuxWindow[] }
```

#### SSH Transport

```typescript
hostExec(host: string, cmd: string): Promise<string>
listSessions(host: string): Promise<Session[]>
capture(host: string, target: string): Promise<string>
sendKeys(host: string, target: string, keys: string): Promise<void>
getPaneCommand(host: string, target: string): Promise<string>
getPaneCommands(host: string, target: string): Promise<string[]>
getPaneInfos(host: string, target: string): Promise<PaneInfo[]>
attachRemoteSession(opts: AttachRemoteSessionOptions): Promise<void>

// Types
type HostExecTransport = { host: string; method: "ssh" | "local" }
class HostExecError extends Error { }
class SshAttachError extends Error { }
```

#### HTTP Fetch

```typescript
curlFetch(url: string, init?: RequestInit): Promise<Response>
```

#### Federation & Routing

```typescript
getPeers(): Peer[]
getFederationStatus(): FederationStatus
findPeerForTarget(target: string): Peer | null
resolveTarget(query: string, config: MawConfig): ResolveResult
resolveOracle(name: string, opts?: ResolveOracleOptions): Promise<OracleRef | null>
pickOracle(candidates: OracleRef[], opts?: PickOracleOptions): Promise<OracleRef>

// Types
type ResolveResult =
  | { type: "local"; target: string }
  | { type: "peer"; peerUrl: string; target: string; node: string }
  | { type: "self-node"; target: string }
  | { type: "error"; reason: string; detail: string; hint?: string }
  | null
```

### Fleet & Oracle Management

```typescript
// Fleet operations
FLEET_DIR: string
CONFIG_DIR: string
MAW_ROOT: string
CONFIG_FILE: string
scanWorktrees(): Worktree[]
cleanupWorktree(name: string): void
saveTabOrder(order: string[]): void
restoreTabOrder(): string[]

// Snapshots
takeSnapshot(name: string): Promise<void>
listSnapshots(): Snapshot[]
loadSnapshot(name: string): void
latestSnapshot(): Snapshot | null

// Audit & logging
readAudit(lines?: number): AuditLog[]
logAudit(message: string, meta?: Record<string, any>): void

// Oracle registry
scanLocal(): OracleEntry[]
scanRemote(): Promise<OracleEntry[]>
scanFull(): Promise<OracleEntry[]>
scanAndCache(): Promise<OracleEntry[]>
readCache(): RegistryCache | null
isCacheStale(): boolean

// Manifest
loadManifest(name: string): Promise<OracleManifestEntry | null>
findOracle(query: string): OracleManifestEntry | null
loadManifestCached(): OracleManifestEntry[]
invalidateManifest(): void
ORACLE_MANIFEST_DEFAULT_TTL_MS: number

// Oracle members
loadOracleRegistry(): OracleTeamRegistry
getOracleMembers(oracleName: string): OracleMember[]
filterMembers(members: OracleMember[], filter: string): OracleMember[]
```

### Artifacts

```typescript
createArtifact(meta: ArtifactMeta): Promise<Artifact>
updateArtifact(id: string, update: Partial<ArtifactMeta>): Promise<void>
writeResult(id: string, result: any): Promise<void>
addAttachment(id: string, file: Buffer, name: string): Promise<void>
listArtifacts(query?: string): Artifact[]
getArtifact(id: string): Artifact | null
artifactDir(): string

// Types
interface ArtifactMeta {
  id: string;
  title: string;
  content?: string;
  tags?: string[];
  attachments?: string[];
}
interface ArtifactSummary {
  id: string;
  title: string;
  created: number;
}
```

### Plugins

```typescript
discoverPackages(): LoadedPlugin[]
importPluginSymbol(pluginName: string, symbolName: string): Promise<unknown>
invokePlugin(name: string, ctx: InvokeContext): Promise<InvokeResult>
parseManifest(text: string): PluginManifest
loadManifestFromDir(dir: string): PluginManifest
registerCommand(name: string, handler: CommandHandler): void
matchCommand(args: string[]): CommandMatch | null
listCommands(): string[]
```

### Messages & Queue

```typescript
loadPending(): PendingMessage[]
loadPendingById(id: string): PendingMessage | null
savePending(msg: PendingMessage): void
updatePending(id: string, update: Partial<PendingMessage>): void
deletePending(id: string): void
isExpired(msg: PendingMessage): boolean
pendingDir(): string
pendingPath(id: string): string
TTL_MS: number

// Types
interface PendingMessage {
  id: string;
  from: string;
  to: string;
  body: string;
  timestamp: number;
  ttl?: number;
}
```

### Channels

```typescript
loadOracleChannels(oracleStem: string): OracleChannelConfig | null
saveOracleChannels(oracleStem: string, config: OracleChannelConfig): void
listAllOracleChannels(): OracleChannelConfig[]
loadRepoChannels(repoPath: string): OracleChannelConfig | null
saveRepoChannels(repoPath: string, config: OracleChannelConfig): void
getChannelEnv(oracleStem: string): Record<string, string>

// Types
interface ChannelPlugin {
  id: string;
  env?: Record<string, string>;
}
interface OracleChannelConfig {
  plugins: ChannelPlugin[];
  token_source?: string;
  permissionMode?: "skip" | "relay";  // Default "skip"
}
```

### Workspace

```typescript
cmdWorkspaceCreate(name: string): Promise<void>
cmdWorkspaceJoin(name: string): Promise<void>
cmdWorkspaceShare(name: string, peers: string[]): Promise<void>
cmdWorkspaceUnshare(name: string, peers: string[]): Promise<void>
cmdWorkspaceLs(): Promise<Workspace[]>
cmdWorkspaceAgents(workspaceName: string): Promise<Agent[]>
cmdWorkspaceInvite(workspaceName: string, users: string[]): Promise<void>
cmdWorkspaceLeave(workspaceName: string): Promise<void>
cmdWorkspaceStatus(workspaceName: string): Promise<WorkspaceStatus>
```

### Utilities

```typescript
parseFlags(argv: string[]): Record<string, any>
ghqFind(query: string): Promise<string[]>
ghqList(): Promise<string[]>
ghqFindSync(query: string): string[]
ghqListSync(): string[]
UserError: Error subclass for user-facing errors
isUserError(err: unknown): boolean
assertValidOracleName(name: string): void
validateNickname(nickname: string): boolean
writeNickname(oracleName: string, nickname: string): void
setCachedNickname(oracleName: string, nickname: string): void
sparkline(values: number[], width?: number): string
tlink(text: string, href?: string): string    // Terminal link helper
```

### Runtime & Hooks

```typescript
runHook(name: string, context: any): Promise<any>
runSleepLifecycleHooks(context: SleepLifecycleContextInput): Promise<LifecycleRunSummary>
getTriggers(): Trigger[]
getTriggerHistory(triggerId: string): TriggerEvent[]

interface SleepLifecycleContextInput {
  oracle: string;
  reason: string;
  session?: string;
}
interface LifecycleRunSummary {
  success: boolean;
  pluginsRun: string[];
  errors?: Record<string, string>;
}
```

---

## Plugin System

### Plugin Manifest (plugin.json)

Every plugin package contains a `plugin.json` descriptor:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "sdk": "^26.0.0",
  "entry": "src/index.ts",
  "tier": "standard",
  "weight": 50,
  "cli": {
    "command": "myplugin",
    "aliases": ["mp"],
    "help": "My custom plugin",
    "flags": {
      "verbose": "boolean",
      "output": "string",
      "port": "number"
    }
  },
  "hooks": {
    "on": ["oracle:wake", "oracle:sleep"],
    "gate": ["command:pre"],
    "filter": ["message:in"],
    "late": ["command:post"]
  },
  "capabilities": ["myns:list", "myns:create"],
  "dependencies": {
    "plugins": ["other-plugin"]
  },
  "transport": {
    "peer": true
  }
}
```

### Plugin File Structure

```
~/.maw/plugins/my-plugin/
├── plugin.json                  # Manifest
├── src/
│   └── index.ts                 # Entry point
├── package.json                 # Dependencies (npm)
└── dist/
    └── index.js                 # Built artifact (if compiled)
```

### Plugin Lifecycle Hooks

**Phase 0: GATE** — Return `false` to cancel the pipeline.

```typescript
onGate?(event: any): boolean
```

**Phase 1: FILTER** — Modify the event before handlers.

```typescript
onFilter?(event: any): any
```

**Phase 2: HANDLE** — Observe or react to events. Most plugins use this.

```typescript
onEvent?(event: any): void | Promise<void>
```

**Phase 3: LATE** — Guaranteed cleanup. Runs even if an earlier phase throws.

```typescript
onLate?(event: any): void
```

### Plugin Installation Hooks

```typescript
onInstall?(): void | Promise<void>    // Called when plugin is first installed
onUninstall?(): void | Promise<void>  // Called when plugin is removed
```

### Plugin Discovery

Plugins are discovered from `~/.maw/plugins/` directory. Each subdirectory must contain:
- `plugin.json` with valid manifest
- Either `src/index.ts` (TS plugin) or `*.wasm` (WASM plugin)

Phase A (current) supports `"js"` target only. `"wasm"` is reserved for Phase C.

### Semver Gating

- Manifest `sdk` field specifies required SDK version (e.g., `"^26.0.0"`).
- Plugin loader checks: `manifest.sdk` must satisfy runtime SDK version.
- Mismatch → plugin refused with actionable error.

### Artifact Verification

If `manifest.artifact.sha256` is set and plugin is not a symlink (dev mode):
- On-disk bundle's SHA256 must match declared value.
- Mismatch → plugin refused.
- Symlinked plugins skip hash verification (developer convenience).

### Event Hooks

Hook names follow pattern `namespace:verb`:

| Hook | When | Example |
|------|------|---------|
| `oracle:wake` | Oracle starts | Broker listens on new node |
| `oracle:sleep` | Oracle stops | Cleanup remote resources |
| `command:pre` | Before command dispatch | Validate permissions |
| `command:post` | After command returns | Log results |
| `message:in` | Incoming message | Filter spam |
| `message:out` | Outgoing message | Add metadata |
| `session:create` | New tmux session | Bootstrap agent |
| `session:destroy` | Session closed | Cleanup |

---

## HTTP Server & API Endpoints

Runs on `localhost:3456` by default (configurable). Built on Elysia + Bun HTTP.

### Server Startup

```bash
maw serve [port]                    # Start API + UI
maw serve --force-takeover          # Kill existing process on port
maw serve status                    # Check if running
maw serve stop                      # Stop running server
```

### API Structure

All endpoints prefixed with `/api`.

```
GET  /api/config                    # Node config + agents map
GET  /api/fleet-config              # Fleet topology (lineage)
GET  /api/feed                      # Live event stream
GET  /api/federation/status         # Peer reachability

POST /api/send                      # Send message to agent
GET  /api/sessions                  # List tmux sessions
GET  /api/worktrees                 # List worktrees

POST /api/oracle/wake               # Start oracle
POST /api/oracle/sleep              # Stop oracle
POST /api/oracle/register           # Register new oracle

POST /api/plugins/install           # Install plugin
POST /api/plugins/uninstall         # Uninstall plugin
GET  /api/plugins                   # List installed plugins

POST /api/workspace/create          # Create workspace
POST /api/workspace/join            # Join workspace
GET  /api/workspace/status          # Workspace status
```

### CORS & Auth

- CORS enabled for federation clients.
- Federation auth: HMAC-SHA256 signature verification.
- Private network access header enabled.

### Swagger Documentation

API docs available at:
```
http://localhost:3456/api/docs
```

Title: "maw-js API v2.0.0-alpha.1"

---

## Federation Protocol

### Overview

Nodes communicate via HTTP federation. A node can name peers in its config:

```json
{
  "namedPeers": [
    { "name": "mba", "url": "http://10.20.0.3:3457" },
    { "name": "white", "url": "http://10.20.0.7:3456" }
  ]
}
```

### The v1 Quartet (Stable Public Contract)

Four endpoints define the federation API that UI clients depend on.

#### `GET /api/config`

**Purpose**: Node identity + full aggregated agents map in one call.

**Response**:
```json
{
  "node": "oracle-world",
  "host": "local",
  "port": 3456,
  "ghqRoot": "/home/neo/Code/github.com",
  "oracleUrl": "http://localhost:47779",
  "namedPeers": [
    { "name": "mba", "url": "http://10.20.0.3:3457" }
  ],
  "agents": {
    "mawjs-oracle": "local",
    "homekeeper": "mba"
  },
  "federationToken": "2QHm••••••••••••",
  "commands": {},
  "sessions": {},
  "env": {}
}
```

**Load-bearing fields for UI clients**:
- `node` — local node name
- `agents` — `Record<agentName → nodeName>`
- `namedPeers` — `Array<{ name, url }>`

#### `GET /api/fleet-config`

**Purpose**: Fleet topology with lineage information.

**Response**:
```json
{
  "configs": [
    {
      "name": "101-mawjs",
      "windows": [{ "name": "mawjs-oracle", "repo": "Soul-Brews-Studio/mawjs-oracle" }],
      "sync_peers": ["boonkeeper"]
    },
    {
      "name": "103-skills-cli",
      "windows": [{ "name": "skills-cli-oracle", "repo": "Soul-Brews-Studio/skills-cli-oracle" }],
      "budded_from": "mawjs",
      "budded_at": "2026-04-10T03:50:00.000Z"
    }
  ]
}
```

**Load-bearing fields**:
- `configs[].name` — session slot
- `configs[].windows[].name` — agent name
- `configs[].budded_from` — parent oracle name (optional)

#### `GET /api/feed`

**Purpose**: Live event stream (messages, state changes).

**Query params**:
- `?limit=100` — max events to return
- `?since=<ts>` — events after timestamp
- `?filter=<pattern>` — filter by event type

**Event types**:
- `message:in` / `message:out`
- `oracle:wake` / `oracle:sleep`
- `session:create` / `session:destroy`
- `command:invoke` / `command:done`

#### `GET /api/federation/status`

**Purpose**: Peer reachability + per-peer enrichment.

**Response**:
```json
{
  "self": {
    "node": "oracle-world",
    "reachable": true,
    "latency": 0,
    "version": "26.6.8-alpha.1320"
  },
  "peers": [
    {
      "node": "mba",
      "url": "http://10.20.0.3:3457",
      "reachable": true,
      "latency": 45,
      "version": "26.6.8-alpha.1320",
      "agents": ["homekeeper"]
    }
  ]
}
```

### Routing Resolution Order

When resolving a target like `maw hey neo message`:

1. **Local** — Is "neo" a local tmux window? → `{ type: "local" }`
2. **Node prefix** — Is it `node:neo`? → `{ type: "peer", peerUrl, node }`
3. **Manifest** — Does the oracle manifest list "neo"? → `{ type: "peer", peerUrl, node }`
4. **Agents map** — Is "neo" in `config.agents`? → `{ type: "peer", peerUrl, node }`
5. **Peer alias** — Is "neo" a peer name in `peers.json`? → `{ type: "peer", peerUrl, node }`
6. **Null** — Not found. Caller handles peer discovery.

### Identity & Continuity

Each node has:
- **Name** (`config.node`) — human-readable identifier
- **Federation token** — HMAC shared secret for auth
- **Ed25519 keypair** — (Phase O6+) for per-peer signing
- **Clock** — monotonic counter for message ordering

---

## Channel System

Channels enable oracles to receive commands via external services (Discord, Slack, etc.).

### Configuration

Global channels config:
```
~/.claude/channels/<oracle-stem>/config.json
```

Or per-repo:
```
<repo-path>/.claude/channel.json
```

**Repo-local config takes precedence over global.**

### Schema

```typescript
interface OracleChannelConfig {
  plugins: ChannelPlugin[];
  token_source?: string;
  permissionMode?: "skip" | "relay";
}

interface ChannelPlugin {
  id: string;                    // Plugin name (e.g., "discord-bot")
  env?: Record<string, string>;  // Plugin env vars (e.g., DISCORD_BOT_TOKEN)
}
```

### Permission Modes

- `"skip"` (default) — Inject `--dangerously-skip-permissions` (autonomous)
- `"relay"` — Omit skip flag; permission prompts flow through the channel (MCP relay)

### Loading Strategy

```typescript
loadEffectiveChannels(repoPath: string, oracleStem: string): OracleChannelConfig | null
```

1. Check repo-local `<repoPath>/.claude/channel.json` → if present, return it
2. Check global `~/.claude/channels/<stem>/config.json` → if present, return it
3. Return `null` (no channel configured)

### Token Sources

`token_source` field hints where channel tokens come from:
- `"env"` — from environment variables
- `"1password"` — from 1Password CLI
- `"vault"` — from Vault
- Custom string — user-defined

---

## Extension Points & Hooks

Plugins can hook into four event phases and two lifecycle stages.

### Event Phases

#### Phase 0: GATE
Return `false` to cancel the entire event pipeline.

```typescript
onGate(event: any): boolean
```

Plugins with lowest weight execute first. Stops at first rejection.

#### Phase 1: FILTER
Modify or enrich the event before handlers see it.

```typescript
onFilter(event: any): any
```

Transformed event flows to Phase 2. Multiple filters chain.

#### Phase 2: HANDLE
Observe or react to events. Main plugin logic lives here.

```typescript
onEvent(event: any): void | Promise<void>
```

All handlers in this phase execute; failures don't block others.

#### Phase 3: LATE
Cleanup phase. Runs even if Phase 2 throws.

```typescript
onLate(event: any): void
```

Guaranteed to run. Exceptions swallowed.

### Lifecycle Hooks

#### Oracle Wake
Fires when an oracle starts (session created, AI agent ready).

```typescript
// In plugin.json
{
  "hooks": {
    "wake": {
      "script": "src/on-wake.ts",
      "handler": "setupOracle",
      "ensures": ["broker:listening"],
      "policy": "fail-fast"
    }
  }
}
```

#### Oracle Sleep
Fires when an oracle stops (cleanup time).

```typescript
{
  "hooks": {
    "sleep": {
      "script": "src/on-sleep.ts",
      "handler": "cleanup",
      "policy": "best-effort"
    }
  }
}
```

#### Plugin Serve
Runs persistent background process (e.g., HTTP server, message broker).

```typescript
{
  "hooks": {
    "serve": {
      "script": "src/serve.ts",
      "handler": "startServer",
      "ensures": ["http:3000", "mqtt:1883"]
    }
  },
  "engine": {
    "serve": {
      "command": "node src/serve.js",
      "prefix": "/api/my-service",
      "health": "/health",
      "events": ["oracle:wake", "oracle:sleep"],
      "eventPath": "/events"
    }
  }
}
```

### Cron Jobs

Run handlers on a schedule:

```typescript
{
  "cron": {
    "schedule": "0 */12 * * *",      // Every 12 hours
    "handler": "onTick"
  }
}

export async function onTick(ctx: InvokeContext): Promise<InvokeResult> {
  // Runs on schedule
  return { ok: true };
}
```

---

## Transport Layer

Abstraction for delivering messages across the mesh.

### Transport Types

#### Local: tmux
Fast path for same-machine targets. ~50ms capture loop.

```typescript
import { tmux } from "@maw-js/sdk";

const session = await tmux.getSession("main");
const window = session.windows[0];
await tmux.sendKeys(`${session.name}:${window.id}`, "echo hello");
```

#### Remote: HTTP Federation
For peer-to-peer messaging.

```typescript
const peers = getPeers();
const target = {
  oracle: "neo",
  host: "remote-host",
  peerUrl: "http://10.20.0.7:3456"
};
// maw resolves and sends via HTTP
```

#### Future: MQTT
Message broker for mesh-wide orchestration (Phase 2).

### Transport Routing

```typescript
resolveTarget(query: string, config: MawConfig): ResolveResult

// Returns one of:
// { type: "local", target: "session:window:pane" }
// { type: "peer", peerUrl: "http://...", target: "...", node: "..." }
// { type: "self-node", target: "..." }
// { type: "error", reason: "...", detail: "..." }
// null
```

### Result Classification

```typescript
classifyError(err: unknown): { reason: TransportFailureReason; retryable: boolean }

type TransportFailureReason =
  | "timeout"      // Network timeout
  | "unreachable"  // Host/peer down
  | "auth"         // Authentication failed
  | "rate_limit"   // Too many requests
  | "rejected"     // Peer rejected message
  | "parse_error"  // Malformed response
  | "unknown";     // Unclassified
```

---

## Creating a Plugin

### Step 1: Scaffold

```bash
mkdir my-plugin && cd my-plugin
cat > plugin.json <<'EOF'
{
  "name": "my-plugin",
  "version": "1.0.0",
  "sdk": "^26.0.0",
  "entry": "src/index.ts",
  "cli": {
    "command": "myplugin",
    "help": "My custom command"
  }
}
EOF

mkdir -p src
cat > src/index.ts <<'EOF'
import { definePlugin } from "@maw-js/sdk";

export default definePlugin({
  name: "my-plugin",
  async handler(ctx) {
    return { ok: true, output: "Hello from my plugin!" };
  }
});
EOF
```

### Step 2: Install as Dependency

```bash
npm init -y
npm install @maw-js/sdk
```

### Step 3: Types

Define `InvokeContext` and `InvokeResult` from the SDK:

```typescript
import type { InvokeContext, InvokeResult } from "@maw-js/sdk";

async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const { source, args, flags, writer } = ctx;

  if (source === "cli") {
    writer?.(`Got ${args.length} args`);
  }

  return {
    ok: true,
    output: JSON.stringify(args)
  };
}
```

### Step 4: Handle Multiple Sources

```typescript
export default definePlugin({
  name: "my-plugin",
  async handler(ctx) {
    switch (ctx.source) {
      case "cli":
        // Handle CLI: ctx.writer is available
        ctx.writer?.("Running from CLI");
        return { ok: true };

      case "api":
        // Handle HTTP POST /api/plugins/my-plugin
        // ctx.writer is undefined; use output field
        return { ok: true, output: "API response" };

      case "peer":
        // Handle federation: maw hey plugin:my-plugin
        return { ok: true, output: "From peer" };
    }
  }
});
```

### Step 5: Use SDK APIs

```typescript
import {
  tmux,
  loadConfig,
  getPeers,
  invokePlugin,
  listCommands
} from "@maw-js/sdk";

export default definePlugin({
  name: "my-plugin",
  async handler(ctx) {
    const config = loadConfig();
    const peers = getPeers();
    const session = await tmux.getSession("main");

    return {
      ok: true,
      output: `Node: ${config.node}, Peers: ${peers.length}`
    };
  }
});
```

### Step 6: Event Hooks (Optional)

```typescript
export default definePlugin({
  name: "my-plugin",
  async handler(ctx) {
    return { ok: true };
  },

  onEvent(event) {
    if (event.type === "oracle:wake") {
      console.log(`Oracle ${event.name} is waking up`);
    }
  },

  onFilter(event) {
    // Enrich events
    event._pluginTime = Date.now();
    return event;
  }
});
```

### Step 7: Install to maw

```bash
# Build if needed (TypeScript plugins don't need build in Phase A)
# Then install
maw plugin install ./my-plugin

# Verify
maw plugin list
```

### Step 8: Invoke

```bash
# CLI
maw myplugin arg1 arg2

# HTTP
curl http://localhost:3456/api/plugins/my-plugin -X POST

# Federation
maw hey neo --via plugin:my-plugin "message"
```

---

## Creating a Command

Commands are top-level CLI subcommands like `maw wake`, `maw send`, `maw ls`.

### Command Registry

Located in `src/cli/command-registry.ts`. Commands can be:
1. Built-in (hardcoded in main CLI)
2. Plugin-provided (via `cli` field in manifest)

### Plugin-Based Command

Simplest approach: declare a CLI command in your plugin manifest.

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "sdk": "^26.0.0",
  "entry": "src/index.ts",
  "cli": {
    "command": "myplugin",
    "aliases": ["mp", "myp"],
    "help": "Do something useful",
    "flags": {
      "verbose": "boolean",
      "output": "string",
      "port": "number"
    }
  }
}
```

Plugin handler receives flags parsed:

```typescript
export default definePlugin({
  name: "my-plugin",
  async handler(ctx) {
    const { args, flags } = ctx;
    const verbose = flags?.verbose as boolean;
    const output = flags?.output as string;

    return {
      ok: true,
      output: `Verbose: ${verbose}, Output: ${output}`
    };
  }
});
```

### Built-in Command

For commands that don't live in plugins, add to `src/commands/`:

```
src/commands/my-command/
├── index.ts          # Export command function
└── impl.ts           # Implementation
```

Register in `src/cli/command-registry.ts`:

```typescript
registerCommand("my-command", {
  handler: myCommandHandler,
  help: "Description",
  flags: { /* ... */ }
});
```

### Command Matching

```typescript
matchCommand(argv: string[]): { name: string; matched: string; rest: string[] } | null

// Input: ["maw", "myplugin", "--verbose", "arg1"]
// Output: { name: "my-plugin", matched: "myplugin", rest: ["arg1"], flags: { verbose: true } }
```

### Aliases

Plugins support multiple names via `aliases`:

```json
{
  "cli": {
    "command": "myplugin",
    "aliases": ["mp", "myp"]
  }
}
```

Now all three work:
```bash
maw myplugin
maw mp
maw myp
```

---

## Summary

**maw-js** is a federated agent orchestration system with:

- **Stable SDK** for plugin authors (`@maw-js/sdk`)
- **Rich plugin system** with hooks, lifecycle, cron, module exports
- **HTTP API** for remote control (federation, UI)
- **Transport abstraction** (local tmux, remote HTTP, future MQTT)
- **Consent & security** gates for permission-driven workflows
- **Channel system** for external integrations (Discord, Slack)
- **Fleet management** with lineage, snapshots, audit logs

For plugin authors: import from `@maw-js/sdk`, define a manifest, implement a handler. That's it.

For infrastructure teams: run `maw serve`, point peers at it, orchestrate the mesh.

For UI developers: consume the v1 federation quartet (`/api/config`, `/api/fleet-config`, `/api/feed`, `/api/federation/status`).
