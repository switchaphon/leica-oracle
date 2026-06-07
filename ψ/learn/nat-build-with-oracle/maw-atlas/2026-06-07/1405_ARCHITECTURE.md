# maw-atlas Architecture Deep Dive

**Version**: 1.0.0  
**Date**: 2026-06-07  
**Repo**: nat-build-with-oracle/maw-atlas

---

## Overview

`maw-atlas` is a **Discord fleet orchestration plugin** for the maw framework. It provides:
- Discord REST API abstraction layer
- Channel/thread/guild management commands
- Auto-spawn workers from Discord threads (watch → route → spawn-session pipeline)
- Bi-directional message bridging (Discord ↔ Codex panes via routing table)
- Team charter integration for worker teams

**Core role**: Tier 2–3 orchestrator — converts Discord activity into tmux sessions + git worktrees, and syncs pane output back to Discord threads.

---

## Directory & File Organization

```
maw-atlas/
├── index.ts                    # Main dispatcher + command routing
├── plugin.json                 # maw plugin metadata
│
├── lib/                        # Core abstractions
│   ├── discord.ts             # Discord REST API client (low-level methods)
│   ├── watch-guards.ts        # Security/access gates for watch command
│   ├── repo.ts                # Atlas-oracle repo resolver (ghq-aware)
│   └── reverse-bridge.ts      # Codex pane → Discord thread bridging
│
└── commands/                   # Command handlers (~1 per file)
    ├── ls.ts                  # List guilds + channels
    ├── read.ts                # Read channel messages (tree + flat)
    ├── whoami.ts              # Bot identity check
    ├── add-guild.ts           # Guild discovery from invite
    ├── backfill.ts            # Backfill channel message history
    ├── threads.ts             # CRUD operations on Discord threads
    ├── slash.ts               # Slash command registration
    ├── avatar.ts              # Bot avatar management
    ├── app.ts                 # Application (bot) settings
    ├── inbox.ts               # Unread message inbox
    ├── serve.ts               # Web dashboard (PARLIAMENT)
    ├── team-threads.ts        # Sync threads from .maw/teams charters
    ├── watch.ts               # [Tier 2] Auto-spawn workers from threads
    ├── route.ts               # [Tier 2] Bi-directional message bridge (daemon/poll)
    └── spawn-session.ts       # [Tier 1] Orchestrate team up + threads + route
```

**Philosophy**: Commands are **thin handlers** — they validate args, delegate to `lib/`, and format output. Lib modules are **testable abstractions** — they own business logic but never do I/O directly (except fetch/Discord API calls).

---

## Core Abstractions

### 1. Discord REST API Client (`lib/discord.ts`)

**Purpose**: Low-level Discord API wrapper. Organized by endpoint domain.

**Key functions**:
- **Identity**: `getMe()`, `getApplication()`
- **Guilds**: `listGuilds()`, `getGuildChannels()`
- **Channels**: `getChannel()`, `createChannel()`, `deleteChannel()`, `moveChannel()`
- **Messages**: `getMessages()`, `postMessage()`
- **Threads**: `createThread()`, `createThreadFromMessage()`, `deleteThread()`, `joinThread()`, `addThreadMember()`, `archiveThread()`
- **Slash Commands**: `listSlashCommands()`, `registerSlashCommands()`, `deleteSlashCommand()`
- **Invites**: `resolveInvite()`
- **Avatar**: `setBotAvatar()`

**Design**:
```typescript
async function request(path: string, token: string, method = "GET", body?: any): Promise<any>
```
- Single `request()` wrapper handles auth, JSON parsing, error handling
- Token fallback: env var → `pass show discord/atlas-oracle-token`
- Errors throw with Discord status code + method + path

**Helpers**:
- `filterTextChannels()`, `filterVoiceChannels()` — type-safe filtering

---

### 2. Watch Guards (`lib/watch-guards.ts`)

**Purpose**: Security and capacity gates for the watch command. Pluggable, composable decisions.

**Key guards**:
- **`allowFromGate()`** — User whitelist check (reads access.json)
- **`maxWorktreesGate()`** — Active worker cap (counts spawn state + agents/ dir)
- **`budgetAlert()`** — Threshold warning (e.g., "8+ active, issue warning")
- **`sanitizeThreadName()`, `sanitizeBranchName()`** — Cleanup + validation
- **`cleanupArchivedThreads()`** — Kill panes + remove worktrees for archived threads

**Input shape** (type-driven):
```typescript
type AllowFromInput = { userId?, channelId?, thread?, accessPath: string };
type MaxWorktreesInput = { activeWorkers?, maxWorktrees?, worktreeRoot?, state? };
type GuardDecision = { ok: boolean; reason?: string; warning?: string };
```

**Usage in watch.ts**:
```typescript
const guards = watchGuards;  // import the whole module
const allowed = await guards.allowFromGate({ userId, thread, channelId, accessPath }, ...);
// Allows override or fallback implementations
```

---

### 3. Repository Resolver (`lib/repo.ts`)

**Purpose**: Find the Atlas-oracle repo on this machine (ghq-aware, multi-candidate).

**Single function**:
```typescript
export function findAtlasRepo(): string | null
```

**Logic**:
1. Run `ghq root` to get ghq base
2. Check candidates in order:
   - `{ghqRoot}/github.com/Soul-Brews-Studio/discord-oracle`
   - `{ghqRoot}/github.com/Soul-Brews-Studio/atlas-oracle`
3. Verify by checking `parliament/api/server.ts` exists
4. Return first match or null

**Used by**: watch, route, backfill (to find `.discord/`, `.maw/` paths)

---

### 4. Reverse Bridge (`lib/reverse-bridge.ts`)

**Purpose**: Codex pane output → Discord thread (optional, not integrated into main flow yet).

**Key functions**:
- **`peekPane(pane: string)`** — Get current pane content via `maw peek`
- **`diffOutput(previous, current)`** — Delta-compress (skip if unchanged)
- **`runReverseBridgeOnce()`** — Poll all panes, post diffs to Discord

**Data shapes**:
```typescript
type ReverseRouteEntry = { name?, pane: string; agent? };
type ReverseBridgeSnapshot = { panes: Record<string, string>; lastPostedAt? };
type ReverseBridgeResult = { checked: number; changed: number; posted: number };
```

**Diff strategy**:
- If `current == previous`: skip (no change)
- If `!previous`: seed snapshot, optionally post (replay mode)
- If `current.startsWith(previous)`: post only the new tail
- Otherwise: post full `current` (fallback for large edits)

---

## Plugin Interface

### `plugin.json`

```json
{
  "name": "atlas",
  "entry": "./index.ts",
  "cli": { "command": "atlas", "aliases": ["at"] },
  "capabilities": ["fs:read", "fs:write"],
  "weight": 50
}
```

**Loaded by maw at startup**; CLI will auto-complete `maw atlas <cmd>`.

### Plugin Handler Signature

```typescript
export default async function handler(ctx: InvokeContext): Promise<InvokeResult>
```

**From maw-js SDK**:
```typescript
type InvokeContext = {
  source: "cli" | "plugin" | "webhook" | ...;
  args: string[] | Record<string, any>;
  writer?: (s: string) => void;  // optional streaming output
};

type InvokeResult = {
  ok: boolean;
  output?: string;     // buffered output (if no writer)
  error?: string;
  exitCode?: number;
};
```

**Usage in index.ts**:
```typescript
const out: string[] = [];
const log = (s: string) => (ctx.writer ? ctx.writer(s) : out.push(s));
const done = (ok: boolean, exitCode = ok ? 0 : 1): InvokeResult =>
  ({ ok, output: ctx.writer ? "" : out.join("\n"), error: ok ? undefined : "", exitCode });
```

---

## Command Dispatcher Pattern

**Entry**: `index.ts` handler

**Flow**:
1. Extract subcommand from `args[0]` (case-insensitive)
2. Check for special flags: `--tree`, `--help`, `-h`
3. Load token only if needed (skip for `serve`, `inbox`, `route`, `watch`, `spawn-session`)
4. Switch on subcommand → call handler
5. Catch errors, return `InvokeResult`

**Token loading**:
```typescript
const token = getToken();  // env → pass fallback
if (!token && !["check", "wake", "vesicle", "route", "watch", "spawn-session"].includes(sub)) {
  return done(false);  // fail if token needed but missing
}
```

**Handler signatures** (all async):
```typescript
export async function ls(log, token) { ... }
export async function read(log, token, args) { ... }
export async function watch(log, token, args) { ... }
```

**Consistency**: All handlers take `(log, token?, args?)` in that order.

---

## Watch Command: Thread Detection + Worker Spawn

### Architecture

```
Discord Guild
  └── Channel (e.g., #atlas-tasks)
       └── Threads (polled every 10s)
            ├── New Thread #task-1 → allowFromGate → maxWorktreesGate
            │    └── Post "spawn codex? reply go"
            │    └── waitForGo(10min) → user replies "go"
            │    └── maw wake atlas-task-1 --branch task-1 --thread {threadId}
            │         └── Outputs pane e.g. "01-atlas:2"
            │    └── updateRoutingTable() → { threadId: { pane: "01-atlas:2", agent: "atlas-task-1", ... } }
            └── Known Thread #task-2 → skip (seen before)
```

### State Management

File: `.maw/atlas-watch/state.json`

```typescript
type WatchState = {
  knownThreads: Record<string, { name: string; seenAt: string }>;
  pending: Record<threadId, { confirmationId?, requestedAt, workerName, branchName }>;
  spawned: Record<threadId, { workerName, pane, spawnedAt }>;
};
```

**Lifecycle**:
1. Poll finds thread → add to `knownThreads`
2. New thread → gates pass → post confirmation → move to `pending`
3. User says "go" → `maw wake` → move to `spawned`
4. Archived → cleanup (kill pane, remove worktree)

### Core Functions

**`watchOnce(log, token, channel, state, guards, args)`**
- Fetch active threads from Discord
- Compare against `state.knownThreads`
- Call `handleNewThread()` for each new one
- Return `{ active, newThreads }`

**`handleNewThread(...)`**
- Check `allowFromGate()` — user allowed?
- Check `maxWorktreesGate()` — capacity?
- Sanitize thread name → branch name
- Post confirmation message "spawn codex? reply go"
- Wait up to 10min for user to reply "go"
- Exec `maw wake atlas-{branch} --branch {branch} --thread {threadId}`
- Parse pane from output
- Update routing table + state

**`waitForGo(token, threadId, afterId, timeoutMs, intervalMs)`**
- Poll thread messages every 5s (default)
- Skip bot messages, skip messages before confirmation
- Match "go" (case-insensitive, trimmed)
- Return true if found within timeout

### Configuration (args)

| Arg | Default | Purpose |
|-----|---------|---------|
| `--interval=N` | 10000 | Poll interval (ms) |
| `--confirm-timeout=N` | 600000 | Wait for go (10 min) |
| `--confirm-interval=N` | 5000 | Poll messages during wait |
| `--max-worktrees=N` | 10 | Capacity cap |
| `--budget-threshold=N` | 8 | Alert threshold |
| `--access=path` | `.discord/access.json` | User allowlist |
| `--routing=path` | `.discord/thread-routing.json` | Routing table |
| `--state=path` | `.maw/atlas-watch/state.json` | Watch state |
| `--worker-name=X` | `atlas-{branch}` | Override agent name |
| `--dry-run` | n/a | Don't execute maw wake |
| `--no-notify` | n/a | Skip maw hey notifications |
| `--notify=pane` | `01-atlas:1` | Notify target pane |

---

## Route Command: Bi-Directional Bridge

### Architecture

```
Routing Table (.discord/thread-routing.json)
  {
    "threadId": { name, pane: "01-atlas:2", agent: "atlas-task-1" },
    ...
  }
       ↓
   route daemon (background process)
       ├── [Forward] Discord thread → maw hey pane
       │    Polls every 5s, posts new messages as formatted text
       └── [Reverse] maw peek pane → Discord thread (optional, not integrated)
```

### Forward Bridge (integrated)

**`pollOnce(log, token, table, lastSeen, opts)`**
- For each route (threadId → pane):
  - Fetch messages after `lastSeen[threadId]` (snowflake ID)
  - Skip bot messages (unless `--include-bots`)
  - For each new message: `maw hey pane "[#threadName · author] content"`
  - Update `lastSeen[threadId] = message.id`
  - Log "forwarded"

**Message formatting**:
```typescript
`[${threadName} · ${author}] ${content}${attachments ? '\n' + attachments : ''}`
```

### Daemon Lifecycle

**`startRouteDaemon(log, args)`**
- Check if PID alive → return (already running)
- Spawn detached child: `maw atlas route daemon`
- Write PID file, status file, log file
- Return `{ ok, pid, alreadyRunning }`

**`stopRouteDaemon(log, args)`**
- Read PID file
- SIGTERM → sleep 100ms × 20 → SIGKILL if `--force`
- Unlink PID file, update status

**`routeStatus(log, args)`**
- Read PID file → check alive
- Read status + last-seen
- List routes with last message time (from snowflake ID)

### Route Sync

**`syncRouteTable(log, token, args)`**
- Read `.maw/teams/*.yaml` charters
- Extract agent names (e.g., `atlas-task-1`)
- Fetch active threads from Discord (`maw atlas threads --json`)
- Match agent → thread by name (with fallback aliases)
- Infer pane: preserved from existing table, or computed from agent ordinal
- Write new routing table

**Candidate thread names** for agent `atlas-task-1`:
- `task-1-workspace`, `task-1`, `atlas-task-1`, `atlas-task-1-workspace`
- `codex-1-workspace`, `codex-1`, `codex`, `codex-workspace` (if ordinal=1)

### Configuration (args)

| Subcommand | Purpose |
|-----------|---------|
| `route start` | Spawn daemon, return to shell |
| `route stop [--force]` | Kill daemon (SIGTERM → SIGKILL) |
| `route status` | List routes + last message time |
| `route sync` | Rebuild routing table from charters |
| `route daemon` | Run polling loop foreground |
| `route watch` | Alias for daemon |
| `route once [--dry-run] [--replay]` | Poll once, exit |

| Option | Default | Purpose |
|--------|---------|---------|
| `--config=path` | `.discord/thread-routing.json` | Routing table |
| `--state=path` | `.maw/atlas-route/last-seen.json` | Last message IDs |
| `--pid-file=path` | `/tmp/maw-atlas-route.pid` | Daemon PID |
| `--status-file=path` | `/tmp/maw-atlas-route.status.json` | Runtime status |
| `--limit=N` | 20 | Messages fetched per thread per poll |
| `--interval=N` | 5000 | Poll interval (daemon/watch) |
| `--replay` | n/a | Process old messages, don't seed latest |
| `--include-bots` | n/a | Forward bot messages too |
| `--dry-run` | n/a | Log without calling maw hey |

---

## Spawn-Session: Tier 1 Orchestrator

### Single Responsibility

Sequentially run three commands in order:
1. `maw team up <charter>` — Deploy team (tmux + agents)
2. `maw atlas team-threads sync` — Create Discord threads
3. `maw atlas route start` — Start message bridge daemon

### Structure

```typescript
type Step = { label: string; argv: string[] };

const steps: Step[] = [
  { label: "team up", argv: ["maw", "team", "up", charter] },
  { label: "team threads sync", argv: ["maw", "atlas", "team-threads", "sync"] },
  { label: "route start", argv: ["maw", "atlas", "route", "start"] },
];
```

**`runStep(step, dryRun, notifyTarget, log)`**
- Log the command
- If dry-run: skip execution, notify
- Else: spawn step, capture output, check exit code
- On failure: notify, throw (stop pipeline)
- On success: notify, continue

### Configuration

| Option | Default | Purpose |
|--------|---------|---------|
| `--dry-run` | n/a | Don't execute steps |
| `--notify=pane` | `01-atlas:1` | Notify target (progress + completion) |
| `--no-notify` | n/a | Skip notifications |

---

## Team Threads: Charter → Discord Sync

### Purpose

Convert `.maw/teams/*.yaml` team charters into Discord threads.

**Reads**: `agents` section from YAML
```yaml
members:
  - role: codex
    name: atlas-task-1
  - role: codex
    name: atlas-task-2
```

**Creates**: One thread per agent:
- Thread name: agent name without `atlas-` prefix
  - `atlas-task-1` → `task-1` thread
- Thread placement: Under `102-atlas-oracle` channel (default) or `--channel` arg
- Starter message: `🌍 task-1 thread — worktree agents/1-atlas-task-1/`

### Key Functions

**`listActiveThreads(token, guildId)`**
- Fetch `/guilds/{guildId}/threads/active` (unfiltered)
- Return array of thread objects

**`resolveChannel(token, input)`**
- If numeric: fetch channel by ID
- Else: search all guilds for channel by name (case-insensitive)
- Return `{ id, guildId }`

**`parseAgentsFromCharter(file)`**
- Regex match `role:` + `name:` lines
- Extract names where role starts with "codex" or name contains "codex"
- Return unique list

---

## Other Commands (Brief Survey)

### Query Commands

**`ls`** — List all guilds + channels
- No args, no token needed
- Loops guilds → channels, counts text/voice

**`read [channel] [--limit=N]`** — Read messages
- Default: `--tree` mode (show all guilds/channels/threads structure)
- With channel: show messages in flat or JSON
- Tree mode: ASCII box drawing, shows threads under parent channels

**`threads`** — Thread CRUD
- `threads create <ch> <name>`
- `threads open <ch> <name>` — With starter message + bot joins
- `threads delete <id>`
- `threads archive <id>`
- `threads join <id>`
- `threads add <id> <user-id>`
- Default: list active threads (JSON or human)

**`backfill [--guild=X] [--limit=N] [--all]`**
- Fetch message history per channel
- Write to `backfill/{guild}/{channel}.json`
- Respects rate limiting (1s delay per channel)
- Delegates to atlas-oracle `backfill-channels.ts` script if found

**`add-guild <invite-or-id>`**
- Discover new guild from invite code
- Resolve invite → guild ID
- Fetch channels (one-shot discovery)

### Settings Commands

**`avatar [set <path>]`**
- Get current avatar
- Set avatar from PNG/JPG/GIF/WebP (base64 encoded)

**`app [interactions <url>]`**
- Get app settings
- Set interactions endpoint URL (for slash command acks)

**`slash [list|register|remove]`**
- List registered slash commands
- Register new commands from code
- Delete commands by name/ID

**`whoami`**
- Simple identity check: fetch `/users/@me` + `/applications/@me`
- Print bot name, ID, avatar

### Utility Commands

**`inbox [--all] [--from=oracle]`**
- List unread inbox messages (from other Oracles)
- Parses `.discord/access.json` for message author
- No token needed (reads from disk)

**`serve [--port=N] [--build]`**
- Start PARLIAMENT web dashboard
- No token needed (static file serving + read-only Discord)

---

## Execution Model & Lifecycle

### Single Invocation Path

```
maw atlas <cmd> [args]
  ↓ (via plugin system)
index.ts:handler(ctx)
  ↓
dispatcher switch(sub)
  ├── [ls] → ls(log, token)
  ├── [read] → read(log, token, args)
  ├── [watch] → watch(log, token, args)         // ← long-running, blocks until --once or Ctrl+C
  ├── [route start] → startRouteDaemon()        // ← spawns detached child
  ├── [route daemon] → routeDaemon()            // ← foreground loop
  └── [spawn-session] → spawnSession(log, args) // ← sequential steps
```

### Process Spawning

**Watch command**:
- Polls Discord every 10s
- On new thread + gates pass: `bun.spawn(["maw", "wake", ...])` or `execFile("maw")`
- Captures stdout/stderr to extract pane number

**Route daemon**:
- Parent: `spawn(..., { detached: true, stdio: [ignore, fd, fd] })` → `child.unref()`
- Writes to log file (redirect stdout/stderr)
- Child runs foreground loop polling Discord every 5s

**Spawn-session**:
- `bun.spawn()` for each step sequentially
- Blocks until each completes

### Error Handling

**Pattern**:
```typescript
try {
  // command logic
  return done(true);
} catch (e) {
  log(`error: ${e instanceof Error ? e.message : String(e)}`);
  return done(false);
}
```

**Discord errors**: 
```typescript
if (!res.ok) throw new Error(`Discord ${res.status} ${method} ${path}`);
```

**File I/O**: 
```typescript
readJson<T>(file, fallback) // silent fallback
writeJson(file, value)       // atomic: write .tmp, rename
```

---

## Data Shapes & Contracts

### Routing Table (`.discord/thread-routing.json`)

```typescript
type RoutingTable = Record<string, RouteEntry>;

type RouteEntry = {
  name?: string;           // "task-1"
  pane: string;            // "01-atlas:2"
  agent?: string;          // "atlas-task-1"
};
```

**Validation**:
- Key must be 17–20 digit snowflake ID
- `pane` must be non-empty string
- Used by: watch (write), route (read/write), team-threads (read for list)

### Access Control (`.discord/access.json`)

```typescript
type AccessConfig = {
  allowFrom: string[];           // global user ID list
  groups?: Record<string, {
    allowFrom: string[];         // per-channel user ID list
  }>;
};
```

**Usage**: Watch command checks `allowFromGate()` before spawning worker.

### Last-Seen State (`.maw/atlas-route/last-seen.json`)

```typescript
type LastSeen = Record<string, string | undefined>;
// threadId → snowflake message ID
```

**Purpose**: Resume polling without re-reading old messages.

**Snowflake utilities**:
- `snowflakeCompare(a, b)` — Compare message IDs (timestamp-aware, bigger = newer)
- `snowflakeToIso(id)` — Extract ISO timestamp from snowflake

---

## Dependencies & Imports

### Internal

```typescript
// index.ts imports all commands
import { watch } from "./commands/watch";
import { route } from "./commands/route";
// ... 14 total

// watch.ts imports lib + Discord
import { getChannel, getGuildChannels, getMessages, ... } from "../lib/discord";
import * as watchGuards from "../lib/watch-guards";
import { findAtlasRepo } from "../lib/repo";

// route.ts imports lib + repo
import { findAtlasRepo } from "../lib/repo";
```

### External

- **`maw-js/plugin/types`** — `InvokeContext`, `InvokeResult` (SDK)
- **Node builtin**: `fs`, `path`, `child_process` (spawn, execFile), `crypto` (potentially)
- **Bun builtin** (fallback for Node): `Bun.spawn()` (faster process spawning)
- **Fetch API** — Discord REST calls (native in Bun + Node 18+)

### No external npm packages

All logic is hand-rolled for minimal dependencies.

---

## Patterns & Conventions

### Argument Parsing

```typescript
function argValue(args: string[], name: string): string | undefined {
  const exact = args.find(a => a.startsWith(`${name}=`));
  if (exact) return exact.slice(name.length + 1);
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : undefined;
}

function intArg(args: string[], name: string, fallback: number): number {
  const raw = argValue(args, name);
  const parsed = raw ? Number.parseInt(raw, 10) : NaN;
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function hasFlag(args: string[], name: string): boolean {
  return args.includes(name);
}
```

**Usage**:
```typescript
const limit = intArg(args, "--limit", 20);
const path = argValue(args, "--config") || DEFAULT_PATH;
if (hasFlag(args, "--dry-run")) { ... }
```

### File I/O Atomicity

```typescript
function writeJson(file: string, value: any) {
  mkdirSync(dirname(file), { recursive: true });
  const tmp = `${file}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`);
  renameSync(tmp, file);  // atomic on POSIX
}
```

**Why**: Prevents partial writes if process crashes.

### Process Spawning (Dual-Mode)

```typescript
async function execText(argv: string[]): Promise<{ code: number; stdout: string; stderr: string }> {
  const bun = (globalThis as any).Bun;
  if (bun?.spawn) {
    // Fast path: Bun.spawn + streaming
    const proc = bun.spawn(argv, { stdout: "pipe", stderr: "pipe" });
    const [code, stdout, stderr] = await Promise.all([
      proc.exited,
      proc.stdout ? new Response(proc.stdout).text() : Promise.resolve(""),
      proc.stderr ? proc.stderr.text() : Promise.resolve(""),
    ]);
    return { code, stdout, stderr };
  }

  // Fallback: Node.js execFile
  return new Promise(resolvePromise => {
    execFile(argv[0], argv.slice(1), { encoding: "utf8", maxBuffer: 1024 * 1024 }, 
      (err, stdout, stderr) => {
        resolvePromise({ 
          code: err && typeof (err as any).code === "number" ? (err as any).code : (err ? 1 : 0), 
          stdout, 
          stderr 
        });
      }
    );
  });
}
```

**Why**: Bun is 2–3× faster; Node fallback ensures compatibility.

### Logging Abstraction

All commands accept `log: (s: string) => void`:
```typescript
export async function ls(log: (s: string) => void, token: string) {
  log("output line");
  log("");  // blank line
}
```

**Benefit**: Testable, agnostic to stdout/streaming/buffer.

---

## Integration Points

### With maw Framework

- **Plugin registration**: `plugin.json` + `index.ts:handler` export
- **Token fallback**: `getToken()` reads `process.env.DISCORD_BOT_TOKEN` then `pass show discord/atlas-oracle-token`
- **Subprocess calls**: Spawns `maw wake`, `maw hey`, `maw peek`, `maw team`, `maw atlas route`

### With Discord

- **API v10**: `https://discord.com/api/v10`
- **Auth**: `Bot {token}` header
- **Polling**: Thread list via `/guilds/{guildId}/threads/active`
- **Message forwarding**: Post to thread, read thread history
- **Thread lifecycle**: Create, delete, archive, join, add members

### With Git/Worktrees

- **Via watch + maw wake**: Triggers `maw wake <agent>` which manages git worktrees
- **Cleanup**: `watch-guards.ts` can call `git worktree remove` for archived threads
- **Charter parsing**: `team-threads.ts` reads `.maw/teams/*.yaml` (YAML regex parsing)

### With Codex Workers

- **Forward bridge**: `route` command reads thread messages, posts to `maw hey <pane> <message>`
- **Reverse bridge**: (optional) Polls `maw peek <pane>`, diffs, posts to Discord
- **Pane notation**: `sessionName:paneIndex` (e.g., `01-atlas:2`)

---

## Security Considerations

### Token Management

- **No hardcoding**: Read from env or `pass` (system password manager)
- **Fallback chain**: `DISCORD_BOT_TOKEN` env → `pass show discord/atlas-oracle-token`
- **Commands that don't need token**: `serve`, `inbox`, `route`, `watch`, `spawn-session` (route/watch/spawn-session can optionally use it)

### User Access Gates

- **allowFromGate()**: Checks `access.json` user ID whitelist
- **maxWorktreesGate()**: Prevents resource exhaustion (cap active workers)
- **Per-channel groups**: `access.groups[channelId].allowFrom` for fine-grained control

### Input Sanitization

- **Thread names**: Remove null bytes, control chars, trim, max 50 chars
- **Branch names**: Lowercase, normalize Unicode, remove special chars, max 50 chars
- **Snowflake validation**: `^\d{17,20}$` regex
- **Channel ID validation**: In `resolveChannel()`, check for 17–20 digit match first

### Atomic File Operations

- `.tmp-{pid}` write, then rename (prevents partial writes)
- Routing table + state updates use atomic rename

---

## Testing Patterns (Inferred)

**No test framework committed**, but design supports:

1. **Unit test Discord lib**:
   ```typescript
   // Mock fetch, test request() error handling
   expect(() => request(...)).toThrow("Discord 401");
   ```

2. **Integration test watch**:
   ```typescript
   // Mock listActiveThreads, test handleNewThread gates
   const result = await handleNewThread(...);
   expect(result.spawned).toBe(true);
   ```

3. **Snapshot test commands**:
   ```typescript
   const logs: string[] = [];
   await ls(log => logs.push(log), mockToken);
   expect(logs).toContain("guild-name");
   ```

---

## Known Limitations & Gaps

1. **Reverse bridge not integrated**: `lib/reverse-bridge.ts` is complete but not wired into any command. Would need a `route reverse` subcommand or separate daemon.

2. **Rate limiting**: No explicit Discord rate limit handling; relies on 1000ms delays in backfill, assumes backoff in `fetch`.

3. **YAML parsing**: Uses regex instead of proper YAML parser (light dependencies philosophy, but fragile).

4. **No auth for PARLIAMENT**: `serve` command doesn't authenticate; relies on network isolation.

5. **Snowflake arithmetic**: Uses `BigInt` comparison; older Node versions may struggle.

6. **Error recovery**: Most commands fail hard on single error; no retry logic.

---

## Deployment & Runtime

### Environment Variables

| Variable | Default | Used by |
|----------|---------|---------|
| `DISCORD_BOT_TOKEN` | (pass fallback) | All commands (token) |
| `DISCORD_THREAD_ROUTING` | `.discord/thread-routing.json` | route, watch |
| `ATLAS_THREAD_ROUTING` | alias for above | route |
| `ATLAS_ACCESS_JSON` | `.discord/access.json` | watch |
| `ATLAS_WATCH_STATE` | `.maw/atlas-watch/state.json` | watch |
| `ATLAS_ROUTE_STATE` | `.maw/atlas-route/last-seen.json` | route |
| `ATLAS_ROUTE_PID_FILE` | `/tmp/maw-atlas-route.pid` | route |
| `ATLAS_ROUTE_STATUS_FILE` | `/tmp/maw-atlas-route.status.json` | route |
| `ATLAS_ROUTE_LOG_FILE` | `/tmp/maw-atlas-route.log` | route |
| `ATLAS_TMUX_SESSION` | `01-atlas` | route (sync) |
| `ATLAS_PANE_BASE` | `2` | route (sync) |
| `MAW_BIN` | `maw` | spawn-session, route sync |
| `DISCORD_STATE_DIR` | `.discord` | backfill (delegation) |

### Typical Deployment Flow

```bash
# 1. Check bot is online
maw atlas whoami

# 2. List existing Discord structure
maw atlas ls

# 3. Start watching a channel for new threads
maw atlas watch "#atlas-tasks" &

# 4. In another terminal, start the message bridge daemon
maw atlas route start

# 5. Deploy a team using a charter
maw atlas spawn-session .maw/teams/project-x.yaml

# 6. Monitor status
maw atlas route status
```

---

## Key Insights

### Design Philosophy

1. **Thin handlers, fat libs**: Commands validate args + format output; libs own logic
2. **Plugin-first**: No CLI binary; entry point is plugin + maw dispatcher
3. **Minimal deps**: No npm packages; self-contained pure TypeScript
4. **Composable gates**: Watch guards pluggable for custom security
5. **State files over sessions**: `.json` files allow resumption, debugging, audit

### Coordination Model

- **Discord as source of truth**: Threads = work units
- **Routing table as contract**: Threads ↔ Panes bidirectional mapping
- **Daemon pattern**: Background process (route) continuously syncs thread messages
- **Charter-driven**: Teams defined in code (`.maw/teams/*.yaml`), not Discord

### Scalability

- **Supports 10–20 active workers** (configurable cap)
- **Polling-based**: No Discord gateway (simpler, stateless)
- **Atomic state updates**: No race conditions
- **Process isolation**: Each worker is tmux pane + git worktree

---

## Summary Table

| Component | Purpose | Key Files | Pattern |
|-----------|---------|-----------|---------|
| Discord API | Low-level REST | `lib/discord.ts` | Organized by endpoint |
| Watch | Auto-spawn workers | `commands/watch.ts` | Poll → gate → post → exec |
| Route | Message bridge | `commands/route.ts` | Daemon + sync + status |
| Spawn-Session | Orchestrator | `commands/spawn-session.ts` | Sequential steps |
| Guards | Security | `lib/watch-guards.ts` | Pluggable decisions |
| Reverse Bridge | Pane → Discord | `lib/reverse-bridge.ts` | Peek → diff → post |
| Dispatcher | CLI entry | `index.ts` | Switch on subcommand |

---

**End of Document**
