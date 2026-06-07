# maw-atlas Public API & Integration Surface

**Repository**: `/Users/switchaphon/ghq/github.com/nat-build-with-oracle/maw-atlas`  
**Version**: 1.0.0  
**Entry Point**: `index.ts` → dispatch handler via maw-js plugin system  
**Language**: TypeScript (Bun runtime)

---

## Plugin Architecture

### Plugin Configuration (`plugin.json`)

```json
{
  "name": "atlas",
  "version": "1.0.0",
  "entry": "./index.ts",
  "sdk": "^1.0.0",
  "description": "Discord fleet infrastructure",
  "author": "atlas-oracle",
  "capabilities": ["fs:read", "fs:write"],
  "cli": {
    "command": "atlas",
    "aliases": ["at"],
    "help": "maw atlas <ls|read|backfill|check|wake|vesicle>"
  },
  "weight": 50,
  "schemaVersion": 1
}
```

### Handler Interface (`InvokeContext` → `InvokeResult`)

Source: `index.ts`, imports from `maw-js/plugin/types`

```typescript
// Handler signature
export default async function handler(ctx: InvokeContext): Promise<InvokeResult>

// Key properties
ctx.source: "cli" | "discord" | "codex" | ...
ctx.args: string[]                           // command arguments
ctx.writer?: (s: string) => void            // streaming output callback

// Return contract
InvokeResult = {
  ok: boolean
  output: string                             // if no writer
  error: string | undefined
  exitCode: 0 | 1
}
```

**Integration Points:**
- Receives dispatch from `maw` CLI via plugin loader
- Dispatches to subcommand handlers (each in `commands/<name>.ts`)
- Output streamed to `ctx.writer` or buffered in string array

---

## CLI Command Tree

All commands dispatch through `maw atlas <sub> [args...]`

### Resource Inspection

#### `ls` — List Guilds & Channels
```bash
maw atlas ls [--json] [--plain]
```
- Lists all Discord guilds (servers) bot has access to
- For each guild, lists text channels
- Returns nested guild/channel structure
- REST: `GET /users/@me/guilds`, `GET /guilds/{guildId}/channels`

#### `read <channel>` — Read Messages
```bash
maw atlas read #channel-name [--limit=N] [--json] [--tree]
maw atlas read 1234567890      # by channel ID
maw atlas read                 # tree mode: full guild structure
```
- `--limit=N`: message count (default 5)
- `--json`: JSON output vs human-readable
- `--tree`: guild/channel/thread tree with recent messages
- Shows last N messages, oldest-to-newest
- REST: `GET /channels/{channelId}/messages?limit={n}`

#### `threads` — Thread Management
```bash
maw atlas threads [--json]                        # list all threads
maw atlas threads create <channel> <name>         # create empty thread
maw atlas threads open <channel> <name>           # create + post starter + join
maw atlas threads delete <thread-name-or-id>
maw atlas threads archive <thread-name>
maw atlas threads join <thread-name>
maw atlas threads add <thread-id> <user-id>
```
- REST endpoints:
  - `POST /channels/{channelId}/threads` (create)
  - `PATCH /channels/{threadId}` (archive)
  - `PUT /channels/{threadId}/thread-members/@me` (bot joins)
  - `PUT /channels/{threadId}/thread-members/{userId}` (add user)

#### `slash` — Application Commands (Slash Commands)
```bash
maw atlas slash list [--json]
maw atlas slash register <name|--all>
maw atlas slash remove <name-or-id>
```
- REST: `GET|PUT|DELETE /applications/{appId}/commands` (global or guild-scoped)

#### `whoami` — Bot Identity
```bash
maw atlas whoami
```
- REST: `GET /users/@me`
- Returns: username, avatar, ID, etc.

#### `avatar` — Bot Avatar Management
```bash
maw atlas avatar
maw atlas avatar set <image-path>     # PNG/JPG/GIF/WebP
```
- REST: `PATCH /users/@me` with base64 avatar
- Converts image to data URI

#### `app` — Application Settings
```bash
maw atlas app
maw atlas app interactions <url>      # set Interactions Endpoint URL
maw atlas app interactions --clear
```
- REST: `GET|PATCH /applications/{appId}`
- For Discord slash command interactions webhook

---

## Fleet Orchestration Commands

### Tier 1: Complete Session Startup

#### `spawn-session <charter>` — Start Full Team Session
```bash
maw atlas spawn-session teams/atlas-m5.yaml [--dry-run] [--notify=01-atlas:1|--no-notify]
```

**Sequentially runs:**
1. `maw team up <charter>` — Spawn team from charter
2. `maw atlas team-threads sync` — Create Discord threads for agents
3. `maw atlas route start` — Start forward/reverse bridge daemon

**Output**: Logs each step, notifies tmux target on completion or error

### Tier 2: Thread-to-Pane Routing

#### `route` — Bridge Discord Threads ↔ Codex Panes
```bash
maw atlas route start [--interval=5000] [--daemon-cmd=maw]
maw atlas route stop [--force]
maw atlas route status [--json]
maw atlas route sync [--charter=path] [--teams-dir=path] [--session=01-atlas] [--pane-base=2]
maw atlas route once [--dry-run] [--replay]
maw atlas route daemon|watch [--interval=5000]
```

**Components:**

**a) Forward Bridge (Discord → Codex)**
- Polls Discord threads for new messages (default interval 5000ms)
- Forwards each message to mapped tmux pane via `maw hey <pane> <message>`
- Caches last-seen message ID per thread
- Configurable message filtering (exclude bots, limit count)

**Files:**
- `.discord/thread-routing.json` — Thread ID → pane mapping
- `.maw/atlas-route/last-seen.json` — Last message ID per thread
- `/tmp/maw-atlas-route.pid` — Daemon process ID
- `/tmp/maw-atlas-route.status.json` — Runtime status + stats

**b) Reverse Bridge (Codex → Discord)**
- Polls codex panes via `maw peek <pane>`
- Diffs output against previous snapshot
- Posts changed output to mapped Discord thread
- Respects Discord 2000-char limit with truncation marker

**Source**: `lib/reverse-bridge.ts`
```typescript
// Public API
export type ReverseRouteEntry = { name?: string; pane: string; agent?: string }
export type ReverseRouteTable = Record<string, ReverseRouteEntry>  // threadId → entry
export type ReverseBridgeOptions = {
  routingPath?: string
  snapshotPath?: string
  maxContentLength?: number
  dryRun?: boolean
  replayInitial?: boolean
}
export type ReverseBridgeResult = { checked: number; changed: number; posted: number }

export function loadReverseRouteTable(file?: string): ReverseRouteTable
export async function runReverseBridgeOnce(log, token, table, options?): Promise<ReverseBridgeResult>
export async function runReverseBridgeFromRouting(log, token, options?): Promise<ReverseBridgeResult>
export async function peekPane(pane: string): Promise<string>
export function diffOutput(previous: string | undefined, current: string): string | null
```

**Routing Table Schema** (`.discord/thread-routing.json`):
```json
{
  "1234567890123456": {
    "name": "codex-1-workspace",
    "pane": "01-atlas:2",
    "agent": "atlas-codex-1"
  }
}
```

**Sync Strategy** (from team charters):
1. Parse `.maw/teams/*.yaml` files
2. Extract agent names from `role: codex` members
3. Query active threads via `maw atlas threads --json`
4. Match agent name → thread by heuristic naming (codex-1 → codex-1-workspace)
5. Infer pane location from existing routing or default session
6. Rebuild routing table with preserved panes

#### `watch <channel>` — Auto-Spawn Workers from New Threads
```bash
maw atlas watch #channel-name [--once] [--dry-run]
  [--interval=10000] [--confirm-timeout=600000]
  [--access=path] [--routing=path] [--max-worktrees=10]
  [--budget-threshold=8] [--notify=01-atlas:1|--no-notify]
```

**Flow:**
1. Poll channel active threads every `--interval` (default 10s)
2. For each new thread:
   a. Check `allowFromGate` — is thread creator in access list?
   b. Check `maxWorktreesGate` — are we below worker cap?
   c. Post confirmation request: "spawn codex? reply go"
   d. Wait up to `--confirm-timeout` for "go" message
   e. Call `maw wake <agent-name> --branch=<sanitized> --thread=<id>`
   f. Parse pane from wake output, update routing table
3. Budget alert if active workers exceed threshold

**State File** (`.maw/atlas-watch/state.json`):
```typescript
type WatchState = {
  knownThreads: Record<string, { name: string; seenAt: string }>
  pending: Record<string, { 
    confirmationId?: string
    requestedAt: string
    workerName: string
    branchName: string
  }>
  spawned: Record<string, {
    workerName: string
    pane: string
    spawnedAt: string
  }>
}
```

### Tier 3: Thread Administration

#### `team-threads` — Sync Threads with Team Charters
```bash
maw atlas team-threads sync [channel]     # create threads for agents
maw atlas team-threads list [channel]     # list existing agent threads
maw atlas team-threads clean [channel]    # archive empty threads
```
- Reads `.maw/teams/*.yaml` charters
- Extracts agent names, creates matching Discord threads
- Default channel: `102-atlas-oracle`
- Posts welcome message with worktree path
- REST: `POST /channels/{channelId}/threads`, `PUT .../thread-members/@me`

#### `add-guild <invite-or-id>` — Register New Guild
```bash
maw atlas add-guild https://discord.gg/xyz123
maw atlas add-guild 1234567890
```
- Resolves invite code or guild ID
- Fetches guild info and channels
- Adds bot to guild if needed

---

## Message Backfill & History

#### `backfill` — Export Discord Messages to JSON
```bash
maw atlas backfill [--guild=name-or-id] [--all] [--list] [--limit=100]
```
- Fetches all text channels from specified guild(s)
- Saves messages to `backfill/<guild>/<channel>.json`
- Can delegate to `atlas-oracle/scripts/backfill-channels.ts` if repo found
- REST: `GET /channels/{channelId}/messages` (paginated, 100 per page)

**Output Structure**:
```json
[
  {
    "id": "1234567890",
    "author": { "id": "...", "username": "alice", "bot": false },
    "content": "...",
    "timestamp": "2026-06-07T14:05:00.000Z",
    "attachments": [...]
  }
]
```

#### `inbox` — Read Oracle Handoff Messages
```bash
maw atlas inbox [--all] [--from=oracle-name] [--mark-read]
```
- Reads `ψ/inbox/*.md` (unread messages from other oracles)
- Default: today's unread only
- `--all`: include past unread
- `--from=name`: filter by sender
- `--mark-read`: set `read: true` in YAML frontmatter

---

## Dashboard & UI

#### `serve` — Start PARLIAMENT Dashboard
```bash
maw atlas serve [--port=4567] [--build]
```
- Serves HTTP dashboard on port 4567 (configurable)
- Auto-builds UI if `--build` or UI not found
- Requires: `atlas-oracle/parliament/app/` and `parliament/api/server.ts`
- Password: `DASHBOARD_PASSWORD` env var (default: "catlab")

**Build:** Runs `bun build` in `parliament/app/` to generate dist/

---

## Discord REST API Layer

Source: `lib/discord.ts` — Low-level REST client

### Token Management
```typescript
export function getToken(): string | null
  // Returns DISCORD_BOT_TOKEN env, or `pass show discord/atlas-oracle-token`
```

### Core Endpoints

**Identity**
```typescript
export async function getMe(token: string): Promise<User>
  // GET /users/@me
```

**Guilds & Channels**
```typescript
export async function listGuilds(token: string): Promise<Guild[]>
  // GET /users/@me/guilds

export async function getGuildChannels(token: string, guildId: string): Promise<Channel[]>
  // GET /guilds/{guildId}/channels

export async function getChannel(token: string, channelId: string): Promise<Channel>
  // GET /channels/{channelId}

export async function createChannel(
  token: string, guildId: string, name: string, type = 0, parentId?: string
): Promise<Channel>
  // POST /guilds/{guildId}/channels

export async function deleteChannel(token: string, channelId: string)
  // DELETE /channels/{channelId}

export async function moveChannel(token: string, channelId: string, parentId: string)
  // PATCH /channels/{channelId}
```

**Messages**
```typescript
export async function getMessages(
  token: string, channelId: string, limit = 100, before?: string
): Promise<Message[]>
  // GET /channels/{channelId}/messages?limit=...&before=...

export async function postMessage(token: string, channelId: string, content: string)
  // POST /channels/{channelId}/messages
```

**Threads**
```typescript
export async function createThread(
  token: string, channelId: string, name: string, autoArchiveDuration = 10080
): Promise<Channel>
  // POST /channels/{channelId}/threads

export async function createThreadFromMessage(
  token: string, channelId: string, messageId: string, name: string, autoArchiveDuration = 10080
): Promise<Channel>
  // POST /channels/{channelId}/messages/{messageId}/threads

export async function deleteThread(token: string, threadId: string)
  // DELETE /channels/{threadId}

export async function joinThread(token: string, threadId: string)
  // PUT /channels/{threadId}/thread-members/@me

export async function addThreadMember(token: string, threadId: string, userId: string)
  // PUT /channels/{threadId}/thread-members/{userId}

export async function archiveThread(token: string, threadId: string)
  // PATCH /channels/{threadId}
```

**Slash Commands**
```typescript
export async function listSlashCommands(token: string, appId: string, guildId?: string)
  // GET /applications/{appId}/commands or /applications/{appId}/guilds/{guildId}/commands

export async function registerSlashCommands(token: string, appId: string, commands: any[], guildId?: string)
  // PUT same endpoint

export async function deleteSlashCommand(token: string, appId: string, commandId: string, guildId?: string)
  // DELETE specific command
```

**Application Settings**
```typescript
export async function getApplication(token: string, appId: string): Promise<Application>
  // GET /applications/{appId}

export async function updateApplication(token: string, appId: string, data: any)
  // PATCH /applications/{appId}

export async function setBotAvatar(token: string, avatarBase64: string)
  // PATCH /users/@me
```

**Helpers**
```typescript
export function filterTextChannels(channels: Channel[]): Channel[]
  // Filter type === 0 (GUILD_TEXT)

export function filterVoiceChannels(channels: Channel[]): Channel[]
  // Filter type === 2 (GUILD_VOICE)
```

### HTTP Client Internals
```typescript
const API = "https://discord.com/api/v10"
const UA = "maw-atlas/1.0.0"

// All requests use Bot token auth + User-Agent header
async function request(path: string, token: string, method = "GET", body?: any)
  // Throws on non-OK status: `Discord {status} {method} {path}`
```

---

## Guard & Gate System

Source: `lib/watch-guards.ts` — extensible security & validation layer

### Guard Types

```typescript
export type GuardDecision = { ok: boolean; reason?: string; warning?: string }

export type AllowFromInput = {
  userId?: string
  channelId?: string
  thread?: { id?: string; owner_id?: string; parent_id?: string }
  accessPath: string
}

export type MaxWorktreesInput = {
  activeWorkers?: number
  maxWorktrees?: number
  worktreeRoot?: string
  state?: { spawned?: Record<string, unknown> }
}

export type CleanupInput = {
  routes: CleanupRoute[]
  activeThreads: Array<{ id: string; thread_metadata?: { archived?: boolean } }>
  dryRun?: boolean
  worktreeRoot?: string
  log?: (s: string) => void
}
```

### Guard Functions

```typescript
export function allowFromGate(input: AllowFromInput): GuardDecision
  // Check if user ID is in .discord/access.json allowFrom list
  // Reads JSON file: { allowFrom: [userId, ...], groups: { channelId: { allowFrom: [...] } } }

export function maxWorktreesGate(input: MaxWorktreesInput): GuardDecision
  // Check active worker count vs cap (default 10)
  // Counts directories in agents/ matching /codex|atlas/

export function budgetAlert(input: { activeWorkers?; threshold?; state? }): string | void
  // Emit warning if active workers > threshold (default 8)

export async function cleanupArchivedThreads(input: CleanupInput): Promise<CleanupResult>
  // For archived threads: kill maw worker, remove git worktree
  // Executes: maw kill <target>, git worktree remove <path>

export async function autoCleanup(input: CleanupInput): Promise<CleanupResult>
  // Alias for cleanupArchivedThreads
```

### Sanitization Functions

```typescript
export function sanitizeInput(value: string, maxLength = 50): string
  // Strip control chars, collapse whitespace, limit length

export function sanitizeThreadName(name: string, maxLength = 50): string
  // Clean input, fallback to "atlas-thread"

export function sanitizeBranchName(name: string): string
  // Lowercase, normalize unicode, remove special chars, keep a-z0-9._/-
```

### Access Control File (`access.json`)
```json
{
  "allowFrom": ["123456789", "987654321"],
  "groups": {
    "channel_id_1": {
      "allowFrom": ["111111111"]
    }
  }
}
```

---

## Extension Points

### 1. Watch Guards (`watch.ts` → `watch-guards.ts`)
Custom implementations can be registered via dynamic import:
```typescript
const guards = watchGuards  // can be extended with custom guards

// Types available for override:
type GuardDecision = { ok: boolean; reason?; warning? }
export async function allowFromGate(input: AllowFromInput): GuardDecision
export async function maxWorktreesGate(input: MaxWorktreesInput): GuardDecision
export async function budgetAlert(input): string | void
export async function sanitizeThreadName(name: string): string
export async function sanitizeBranchName(name: string): string
export async function cleanupArchivedThreads(input: CleanupInput): Promise<CleanupResult>
```

### 2. Reverse Bridge Customization
Exported types + functions allow custom polling & formatting:
```typescript
export type ReverseRouteEntry = { name?; pane: string; agent? }
export type ReverseBridgeOptions = {
  routingPath?: string
  snapshotPath?: string
  maxContentLength?: number
  dryRun?: boolean
  replayInitial?: boolean
}

// Call directly if needed:
const result = await runReverseBridgeOnce(log, token, table, options)
const result = await runReverseBridgeFromRouting(log, token, options)
```

### 3. Config & Environment Variables

**Routing & State Paths:**
```bash
DISCORD_THREAD_ROUTING     # .discord/thread-routing.json location
ATLAS_THREAD_ROUTING       # alias
ATLAS_ROUTE_STATE          # .maw/atlas-route/last-seen.json
ATLAS_ROUTE_PID_FILE       # /tmp/maw-atlas-route.pid
ATLAS_ROUTE_STATUS_FILE    # /tmp/maw-atlas-route.status.json
ATLAS_ROUTE_LOG_FILE       # /tmp/maw-atlas-route.log
ATLAS_WATCH_STATE          # .maw/atlas-watch/state.json
```

**Auth & API:**
```bash
DISCORD_BOT_TOKEN          # Discord bot token (required for most commands)
DASHBOARD_PASSWORD         # PARLIAMENT UI password (default: "catlab")
ATLAS_TMUX_SESSION         # Default tmux session for routing (default: "01-atlas")
ATLAS_PANE_BASE            # Base pane number for inferred panes (default: 2)
MAW_BIN                    # maw binary path (default: "maw")
ATLAS_TEAMS_DIR            # .maw/teams directory location
```

---

## Data Schemas

### Discord API Objects (Subset)

**Guild**
```typescript
{ id: string; name: string; icon?: string; owner_id?: string; ... }
```

**Channel**
```typescript
{
  id: string
  name: string
  type: 0 | 2 | 4 | 5 | ... // 0=text, 2=voice, 4=category, etc.
  guild_id?: string
  parent_id?: string
  permissions_overwrites?: PermissionOverwrite[]
  ...
}
```

**Thread** (extends Channel)
```typescript
{
  id: string
  name: string
  type: 11 | 12  // 11=public, 12=private
  parent_id: string
  owner_id?: string
  thread_metadata?: {
    archived: boolean
    archiver_id?: string
    auto_archive_duration: number
    archive_timestamp: string
    locked?: boolean
    create_timestamp?: string
  }
  ...
}
```

**Message**
```typescript
{
  id: string
  channel_id: string
  author?: {
    id: string
    username: string
    global_name?: string | null
    avatar?: string
    bot?: boolean
    ...
  }
  content?: string
  timestamp: string  // ISO 8601
  edited_timestamp?: string | null
  attachments?: Array<{
    id: string
    filename: string
    url: string
    size: number
    ...
  }>
  ...
}
```

**Application**
```typescript
{
  id: string
  name: string
  description: string
  interactions_endpoint_url?: string | null
  ...
}
```

---

## Integration Patterns

### Pattern 1: Forward Bridge (Discord → Codex)

```typescript
// 1. Load routing table
const table = loadReverseRouteTable(routingFile)

// 2. Poll loop
while (true) {
  for (const [threadId, route] of Object.entries(table)) {
    const messages = await getThreadMessages(token, threadId, limit, lastSeenId)
    
    for (const msg of messages) {
      if (!msg.content?.trim()) continue
      
      // 3. Forward to pane
      await mawHey(route.pane, formatMessage(route, msg), dryRun)
      lastSeenId[threadId] = msg.id
    }
  }
  
  // 4. Save state
  writeLastSeen(stateFile, lastSeenId)
  
  await sleep(interval)
}
```

### Pattern 2: Reverse Bridge (Codex → Discord)

```typescript
// 1. Load routing table
const table = loadReverseRouteTable(routingFile)
const snapshot = loadSnapshot(snapshotFile)

// 2. Poll loop
for (const [threadId, route] of Object.entries(table)) {
  const current = await peekPane(route.pane)
  const diff = diffOutput(snapshot.panes[route.pane], current)
  
  if (!diff) continue
  
  // 3. Post to Discord
  await postMessage(token, threadId, formatContent(route, diff))
  snapshot.panes[route.pane] = current
}

// 4. Save snapshot
writeJson(snapshotFile, snapshot)
```

### Pattern 3: Watch → Wake → Route

```typescript
// 1. Poll for new threads
const threads = await listActiveThreads(token, guildId, channelId)
const newThreads = threads.filter(t => !state.knownThreads[t.id])

for (const thread of newThreads) {
  // 2. Check gates
  const allowed = await allowFromGate({ userId: thread.owner_id, thread, ... })
  if (!allowed.ok) continue
  
  // 3. Request confirmation
  await postMessage(token, thread.id, "spawn codex? reply go")
  state.pending[thread.id] = { workerName, branchName, requestedAt: ... }
  
  // 4. Wait for go
  const go = await waitForGo(token, thread.id, confirmationId, 10 * 60_000, 5_000)
  if (!go) continue
  
  // 5. Wake worker
  const result = await execText(["maw", "wake", workerName, "--branch", branchName])
  const pane = parsePane(result.stdout, fallback)
  
  // 6. Record routing
  updateRoutingTable(routingFile, thread, pane, workerName)
  state.spawned[thread.id] = { workerName, pane, spawnedAt: ... }
}
```

---

## Error Handling & Diagnostics

### Discord API Errors
```typescript
// HTTP non-200 response
throw new Error(`Discord ${res.status} ${method} ${path}`)
```

**Common Status Codes:**
- 401: Missing/invalid token
- 403: Insufficient permissions
- 404: Resource not found
- 429: Rate limited
- 500: Discord server error

### Logging Pattern
All commands use a `log` callback:
```typescript
export async function command(log: (s: string) => void, token: string, args: string[])
```

Usage: `log("message")` → output via ctx.writer or buffered

### State File Corruption Recovery
```typescript
// JSON parsing failures return fallback
function readJson<T>(file: string, fallback: T): T {
  try { return JSON.parse(readFileSync(file, "utf8")) }
  catch { return fallback }  // graceful degradation
}
```

---

## Performance & Limits

### Discord API Rate Limits
- GET requests: ~10 per second per endpoint
- POST/PATCH/DELETE: ~1 per second per endpoint
- Message history: 100 messages per batch (max limit)
- Thread list per guild: limited to active threads only

### maw-atlas Mitigations
- Backfill: 500ms sleep between channels, 1s between guild batches
- Watch: 10s polling interval (configurable)
- Route: 5s polling interval (configurable)
- Message batches: 100 per fetch, earlier messages require pagination token

### Pane Capacity
- Default max worktrees: 10 (configurable via `--max-worktrees`)
- Budget threshold alert: 8 (configurable via `--budget-threshold`)

---

## File System Layout

```
maw-atlas/
├── index.ts                          # Plugin entry + command dispatch
├── plugin.json                       # Plugin metadata
├── lib/
│   ├── discord.ts                   # Discord REST client
│   ├── reverse-bridge.ts            # Codex→Discord bridge
│   ├── watch-guards.ts              # Security gates + sanitizers
│   └── repo.ts                      # atlas-oracle repo locator
└── commands/
    ├── ls.ts                        # list guilds/channels
    ├── read.ts                      # read messages
    ├── threads.ts                   # thread CRUD
    ├── slash.ts                     # slash commands
    ├── avatar.ts                    # bot avatar
    ├── app.ts                       # app settings
    ├── add-guild.ts                 # guild discovery
    ├── backfill.ts                  # message export
    ├── inbox.ts                     # oracle handoff messages
    ├── whoami.ts                    # bot identity
    ├── serve.ts                     # PARLIAMENT dashboard
    ├── route.ts                     # thread↔pane bridge daemon
    ├── watch.ts                     # auto-spawn from threads
    ├── team-threads.ts              # sync threads + charter
    └── spawn-session.ts             # Tier 1 team startup shortcut
```

---

## Interaction with maw-js & Codex

### maw-js Integration

**Command Invocation:**
```bash
maw atlas <sub> [args...] → plugin handler(ctx: InvokeContext)
```

**Output Contract:**
- If `ctx.writer` provided: stream via callback
- Else: buffer in string array, return as `output` field

### Codex Integration (tmux pane communication)

**Forward (Discord → Codex):**
```bash
maw hey <pane> "<message>"  # via route daemon
```

**Reverse (Codex → Codex output → Discord):**
```bash
maw peek <pane>  # fetch current pane content
```

**Worker Spawning:**
```bash
maw wake <agent-name> --branch=<name> --thread=<threadId>
```

---

## Summary: Public API Surface

### Entry Point
- Plugin handler: `handler(ctx: InvokeContext): Promise<InvokeResult>`
- Dispatches via subcommand name

### Core Interfaces (TypeScript)
- `InvokeContext`, `InvokeResult` (from maw-js/plugin/types)
- `ReverseRouteEntry`, `ReverseRouteTable`, `ReverseRouteOptions` (reverse-bridge.ts)
- `GuardDecision`, `AllowFromInput`, `MaxWorktreesInput`, `CleanupInput` (watch-guards.ts)

### Command Categories
1. **Inspection**: ls, read, threads (list), whoami, avatar, app
2. **Admin**: add-guild, threads (create/delete/archive/join)
3. **Bridge**: route (start/stop/status/sync/daemon), watch, reverse-bridge (exported functions)
4. **Orchestration**: spawn-session, team-threads, watch (guards)
5. **Utility**: backfill, inbox, serve

### REST Endpoints Used
- `GET /users/@me` — bot identity
- `GET /users/@me/guilds` — list guilds
- `GET /guilds/{guildId}/channels` — list channels
- `POST|DELETE /channels/{channelId}` — manage channels
- `GET|POST /channels/{channelId}/messages` — messages
- `POST|DELETE /channels/{channelId}/threads` — thread CRUD
- `PUT /channels/{threadId}/thread-members/@me` — bot joins
- `GET|PUT|DELETE /applications/{appId}/commands` — slash commands
- `GET|PATCH /applications/{appId}` — app settings
- `PATCH /users/@me` — bot avatar

### Extension Points
- Watch guards (allowFromGate, maxWorktreesGate, cleanup functions)
- Reverse bridge (loadReverseRouteTable, runReverseBridgeOnce, diffOutput)
- Config via environment variables (routing paths, auth, session names)

---

*Generated 2026-06-07 at 14:05 by Leica Oracle*
