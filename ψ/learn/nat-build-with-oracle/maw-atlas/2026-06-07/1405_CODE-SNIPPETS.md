# maw-atlas Code Snippets — Core Architecture & Patterns

**Source repo**: `/Users/switchaphon/ghq/github.com/nat-build-with-oracle/maw-atlas/`
**Collected**: 2026-06-07 @ 14:05

---

## 1. Main Entry Point & Command Dispatcher (`index.ts`)

### High-level flow
```typescript
// lines 25-143 (simplified)
export const command = {
  name: "atlas",
  description: "Discord fleet infrastructure — guilds, channels, bots, backfill.",
};

export default async function handler(ctx: InvokeContext): Promise<InvokeResult> {
  const out: string[] = [];
  const log = (s: string) => (ctx.writer ? ctx.writer(s) : out.push(s));
  const done = (ok: boolean, exitCode = ok ? 0 : 1): InvokeResult =>
    ({ ok, output: ctx.writer ? "" : out.join("\n"), error: ok ? undefined : "", exitCode });

  const args = ctx.source === "cli" ? (ctx.args as string[]) : [];
  const sub = args[0]?.toLowerCase();

  // Commands that don't need token
  if (sub === "serve") { await serve(log, args); return done(true); }
  if (sub === "inbox") { await inbox(log, args); return done(true); }

  // Get token from env or pass
  const token = getToken();
  if (!token && !["check", "wake", "vesicle", "route", "watch", "spawn-session"].includes(sub)) {
    log("✗ no DISCORD_BOT_TOKEN — set env or `pass insert discord/atlas-oracle-token`");
    return done(false);
  }

  try {
    switch (sub) {
      case "whoami":    await whoami(log, token!); break;
      case "ls":        await ls(log, token!); break;
      case "threads":   await threads(log, token!, args); break;
      case "route":     await route(log, token || "", args); break;
      case "watch":     await watch(log, token || "", args); break;
      case "spawn-session": await spawnSession(log, args); break;
      // ... other cases
      default:
        log(`unknown: ${sub} — run 'maw atlas --help'`);
        return done(false);
    }
    return done(true);
  } catch (e) {
    log(`error: ${e instanceof Error ? e.message : String(e)}`);
    return done(false);
  }
}
```

**Key pattern**: Thin dispatcher — routes to command handlers in `commands/` based on first arg. Some commands (`route`, `watch`, `spawn-session`) work without token.

---

## 2. Discord REST Client (`lib/discord.ts`)

### Core request wrapper
```typescript
const API = "https://discord.com/api/v10";
const UA = "maw-atlas/1.0.0";

export function getToken(): string | null {
  if (process.env.DISCORD_BOT_TOKEN) return process.env.DISCORD_BOT_TOKEN;
  try {
    const { execSync } = require("child_process");
    return execSync("pass show discord/atlas-oracle-token 2>/dev/null", { encoding: "utf8" }).trim() || null;
  } catch { return null; }
}

async function request(path: string, token: string, method = "GET", body?: any): Promise<any> {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: {
      Authorization: `Bot ${token}`,
      "Content-Type": "application/json",
      "User-Agent": UA,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`Discord ${res.status} ${method} ${path}`);
  const txt = await res.text();
  try { return JSON.parse(txt); } catch { return { raw: txt }; }
}
```

**Key pattern**: Single `request()` wrapper handles all HTTP calls. Errors throw with Discord status + method + path for debugging.

### Guild & Channel APIs
```typescript
export async function listGuilds(token: string) {
  return request("/users/@me/guilds", token);
}

export async function getGuildChannels(token: string, guildId: string) {
  return request(`/guilds/${guildId}/channels`, token);
}

export async function createChannel(token: string, guildId: string, name: string, type = 0, parentId?: string) {
  return request(`/guilds/${guildId}/channels`, token, "POST", {
    name, type, ...(parentId ? { parent_id: parentId } : {}),
  });
}
```

### Messages API
```typescript
export async function getMessages(token: string, channelId: string, limit = 100, before?: string): Promise<any> {
  let path = `/channels/${channelId}/messages?limit=${Math.min(limit, 100)}`;
  if (before) path += `&before=${before}`;
  return request(path, token);
}

export async function postMessage(token: string, channelId: string, content: string) {
  return request(`/channels/${channelId}/messages`, token, "POST", { content });
}
```

### Thread Management APIs
```typescript
export async function createThread(token: string, channelId: string, name: string, autoArchiveDuration = 10080) {
  return request(`/channels/${channelId}/threads`, token, "POST", {
    name, type: 11, auto_archive_duration: autoArchiveDuration,
  });
}

export async function createThreadFromMessage(token: string, channelId: string, messageId: string, name: string, autoArchiveDuration = 10080) {
  return request(`/channels/${channelId}/messages/${messageId}/threads`, token, "POST", {
    name, auto_archive_duration: autoArchiveDuration,
  });
}

export async function joinThread(token: string, threadId: string) {
  const res = await fetch(`https://discord.com/api/v10/channels/${threadId}/thread-members/@me`, {
    method: "PUT", headers: { Authorization: `Bot ${token}`, "User-Agent": "maw-atlas/1.0.0" },
  });
  return { ok: res.ok, status: res.status };
}

export async function archiveThread(token: string, threadId: string) {
  return request(`/channels/${threadId}`, token, "PATCH", { archived: true });
}
```

**Key pattern**: Separate thread create flows:
1. Empty thread: `createThread()` (type 11)
2. From message: `createThreadFromMessage()` (preserves context)
3. Membership: `joinThread()` uses raw fetch (different endpoint pattern)

---

## 3. Thread Management (`commands/threads.ts`)

### Channel resolution (name or ID)
```typescript
async function resolveChannel(token: string, input: string): Promise<string | null> {
  if (/^\d{17,20}$/.test(input)) return input;  // Already a snowflake ID
  const clean = input.replace(/^#/, "").toLowerCase();
  const guilds = await listGuilds(token);
  if (!Array.isArray(guilds)) return null;
  for (const g of guilds) {
    const channels = await getGuildChannels(token, g.id);
    if (!Array.isArray(channels)) continue;
    const match = channels.find((c: any) =>
      c.name?.toLowerCase() === clean ||
      c.name?.toLowerCase().includes(clean)
    );
    if (match) return match.id;
  }
  return null;
}
```

### List active threads across guilds
```typescript
async function listActiveThreads(token: string, guildId: string): Promise<any[]> {
  const res = await fetch(`https://discord.com/api/v10/guilds/${guildId}/threads/active`, {
    headers: { Authorization: `Bot ${token}`, "User-Agent": "maw-atlas/1.0.0" },
  });
  if (!res.ok) return [];
  const data = await res.json() as any;
  return data.threads || [];
}
```

### Thread creation with starter message
```typescript
if (sub === "open") {
  const channel = args[2];
  const name = args.slice(3).filter(a => !a.startsWith("--")).join(" ");
  if (!channel || !name) { log("usage: maw atlas threads open <channel> <thread-name>"); return; }
  const channelId = await resolveChannel(token, channel);
  if (!channelId) { log(`✗ channel not found: ${channel}`); return; }
  const msg = await postMessage(token, channelId, `🤖 **${name}** — thread workspace`);
  const thread = await createThreadFromMessage(token, channelId, msg.id, name);
  await joinThread(token, thread.id);
  log(`✓ #${thread.name} opened (${thread.id}) — with starter message + bot joined`);
  return;
}
```

**Key pattern**: Opens a channel, posts starter message with emoji/title, creates thread from that message, bot joins. Establishes metadata trail in Discord.

---

## 4. Watch Command — Auto-spawn Workers (`commands/watch.ts`)

### Core state machine
```typescript
type WatchState = {
  knownThreads: Record<string, { name: string; seenAt: string }>;
  pending: Record<string, { confirmationId?: string; requestedAt: string; workerName: string; branchName: string }>;
  spawned: Record<string, { workerName: string; pane: string; spawnedAt: string }>;
};
```

### Main watch loop
```typescript
export async function watch(log: Log, token: string, args: string[]) {
  const channelInput = args[1];
  if (!channelInput || channelInput === "help") {
    usage(log);
    return;
  }

  const channel = await resolveChannel(token, channelInput);
  if (!channel) {
    log(`✗ channel not found: ${channelInput}`);
    return;
  }

  const guards = watchGuards;
  const state = loadState(args);
  const notifyTarget = hasFlag(args, "--no-notify") ? null : (argValue(args, "--notify") || DEFAULT_NOTIFY_TARGET);
  log(`watching #${channel.name || channel.id} (${channel.id}) every ${intArg(args, "--interval", DEFAULT_INTERVAL_MS)}ms`);

  while (true) {
    try {
      const result = await watchOnce(log, token, channel, state, guards, args);
      log(`poll: ${result.active} active thread(s), ${result.newThreads} new`);
      if (result.newThreads) await notify(notifyTarget, `[m5:atlas] watch saw ${result.newThreads} new thread(s)...`, log);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      log(`watch error: ${msg}`);
      await notify(notifyTarget, `[m5:atlas] watch error: ${msg}`, log);
    }

    if (hasFlag(args, "--once")) return;
    await sleep(intArg(args, "--interval", DEFAULT_INTERVAL_MS));
  }
}
```

### Single poll cycle
```typescript
async function watchOnce(log: Log, token: string, channel: { id: string; guildId: string }, state: WatchState, guards: WatchGuards, args: string[]) {
  await emitBudgetAlert(guards, state, args, log);

  const threads = await listActiveThreads(token, channel.guildId, channel.id);
  const newThreads = threads.filter(thread => !state.knownThreads[thread.id]);
  
  // Record all seen threads
  for (const thread of threads) {
    state.knownThreads[thread.id] = state.knownThreads[thread.id] || { name: thread.name, seenAt: new Date().toISOString() };
  }
  writeJson(statePath(args), state);

  // Process new threads one at a time
  for (const thread of newThreads) {
    await handleNewThread(log, token, thread, channel.id, state, guards, args);
  }

  return { active: threads.length, newThreads: newThreads.length };
}
```

### New thread handling — confirmation gate
```typescript
async function handleNewThread(
  log: Log,
  token: string,
  thread: ThreadInfo,
  channelId: string,
  state: WatchState,
  guards: WatchGuards,
  args: string[],
) {
  // 1. Check allowFrom gate
  const allowed = await allowFromGate(guards, thread, channelId, args);
  if (!allowed.ok) {
    log(`reject thread ${thread.name} (${thread.id}): ${allowed.reason || "allowFrom denied"}`);
    return;
  }

  // 2. Check max worktrees cap
  const cap = await maxWorktreesGate(guards, state, args);
  if (!cap.ok) {
    log(`reject thread ${thread.name} (${thread.id}): ${cap.reason || "maxWorktrees cap"}`);
    await postMessage(token, thread.id, `cannot spawn codex: ${cap.reason || "max worktrees reached"}`);
    return;
  }

  // 3. Post "spawn codex? reply go" and wait for confirmation
  const safeName = sanitizeThreadName(guards, thread.name);
  const branchName = sanitizeBranchName(guards, safeName);
  const workerName = argValue(args, "--worker-name") || `atlas-${branchName}`;
  const confirmation = await postMessage(token, thread.id, "spawn codex? reply go");
  state.pending[thread.id] = { confirmationId: confirmation?.id, requestedAt: new Date().toISOString(), workerName, branchName };
  writeJson(statePath(args), state);
  log(`confirmation posted: #${thread.name} (${thread.id}) waiting for go`);

  // 4. Poll for "go" message
  const go = await waitForGo(
    token,
    thread.id,
    confirmation?.id,
    intArg(args, "--confirm-timeout", DEFAULT_CONFIRM_TIMEOUT_MS),
    intArg(args, "--confirm-interval", 5_000),
  );
  if (!go) {
    log(`timeout waiting for go: #${thread.name} (${thread.id})`);
    return;
  }

  // 5. Wake worker
  const wakeArgs = ["maw", "wake", workerName, "--branch", branchName, "--thread", thread.id];
  log(`go received; exec ${shellQuote(wakeArgs)}`);
  const wake = hasFlag(args, "--dry-run") ? { code: 0, stdout: `dry-run pane ${workerName}`, stderr: "" } : await execText(wakeArgs);
  if (wake.code !== 0) throw new Error(`maw wake failed: ${wake.stderr || wake.stdout}`.trim());

  // 6. Parse pane from output and record routing
  const pane = parsePane(wake.stdout || wake.stderr, workerName);
  updateRoutingTable(routingPath(args), thread, pane, workerName);
  state.spawned[thread.id] = { workerName, pane, spawnedAt: new Date().toISOString() };
  delete state.pending[thread.id];
  writeJson(statePath(args), state);
  await postMessage(token, thread.id, `codex spawned: ${workerName} → ${pane}`);
  log(`spawned: ${thread.name} (${thread.id}) → ${workerName} / ${pane}`);
}
```

### Waiting for confirmation
```typescript
async function waitForGo(token: string, threadId: string, afterId: string | undefined, timeoutMs: number, intervalMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const messages = await getMessages(token, threadId, 50);
    const hit = Array.isArray(messages) && messages.some((message: any) => {
      if (afterId && snowflakeCompare(message.id, afterId) <= 0) return false;  // Skip old messages
      if (message.author?.bot) return false;  // Ignore bots
      return String(message.content || "").trim().toLowerCase() === "go";
    });
    if (hit) return true;
    await sleep(intervalMs);
  }
  return false;
}
```

**Key pattern**: Watch runs indefinitely, polls active threads every N seconds, detects new threads, applies guards (allowFrom, maxWorktrees), posts confirmation request, waits for user "go", executes `maw wake`, records pane routing. State persisted to JSON between polls.

---

## 5. Route Command — Bridge Discord ↔ Codex Panes (`commands/route.ts`)

### Routing table format
```typescript
type RouteEntry = {
  name?: string;
  pane: string;
  agent?: string;
};

type RoutingTable = Record<string, RouteEntry>;
// Example:
// {
//   "123456789012345678": { name: "codex-1-workspace", pane: "01-atlas:1", agent: "atlas-codex-1" }
// }
```

### Start daemon (supervisor pattern)
```typescript
export async function startRouteDaemon(log: Log, args: string[] = []) {
  const pidFile = pidPath(args);
  const existingPid = readPid(pidFile);
  if (isProcessAlive(existingPid)) {
    log(`✓ route daemon already running (pid ${existingPid})`);
    log(`  pid file: ${pidFile}`);
    return { ok: true, pid: existingPid, alreadyRunning: true };
  }

  const bin = argValue(args, "--daemon-cmd") || process.env.MAW_BIN || "maw";
  const childArgs = bin === "maw"
    ? ["atlas", "route", "daemon", ...daemonArgs(args)]
    : daemonArgs(args);
  const logFile = logPath(args);
  const fd = require("fs").openSync(logFile, "a");
  const child = spawn(bin, childArgs, {
    cwd: process.cwd(),
    detached: true,
    stdio: ["ignore", fd, fd],
    env: {
      ...process.env,
      ATLAS_ROUTE_PID_FILE: pidFile,
      ATLAS_ROUTE_STATUS_FILE: statusPath(args),
      ATLAS_ROUTE_LOG_FILE: logFile,
    },
  });
  child.unref();

  writePid(pidFile, child.pid);
  writeRuntimeStatus(args, {
    pid: child.pid,
    startedAt: new Date().toISOString(),
    lastPollAt: null,
    command: bin,
    args: childArgs,
    routing: routingPath(args),
  });

  log(`✓ route daemon started (pid ${child.pid})`);
  log(`  pid file: ${pidFile}`);
  log(`  log: ${logFile}`);
  return { ok: true, pid: child.pid, alreadyRunning: false };
}
```

### Poll once — forward messages Discord → codex panes
```typescript
async function pollOnce(
  log: Log,
  token: string,
  table: RoutingTable,
  lastSeen: LastSeen,
  opts: { limit: number; includeBots: boolean; dryRun: boolean },
): Promise<number> {
  let forwarded = 0;

  for (const [threadId, route] of Object.entries(table)) {
    const messages = await getThreadMessages(token, threadId, opts.limit, lastSeen[threadId]);
    const ordered = messages.slice().sort((a, b) => snowflakeCompare(a.id, b.id));

    for (const msg of ordered) {
      if (!msg.id) continue;
      lastSeen[threadId] = msg.id;

      const hasContent = !!(msg.content || "").trim();
      const hasAttachments = (msg.attachments || []).length > 0;
      if (!hasContent && !hasAttachments) continue;
      if (!opts.includeBots && msg.author?.bot) continue;

      await mawHey(route.pane, formatForwardMessage(route, msg), opts.dryRun);
      forwarded++;
      log(`${opts.dryRun ? "dry-run" : "forwarded"}: ${route.name || threadId} → ${route.pane} (${msg.id})`);
    }
  }

  return forwarded;
}
```

### Format message for codex
```typescript
function formatForwardMessage(route: RouteEntry, msg: DiscordMessage): string {
  const author = msg.author?.global_name || msg.author?.username || "discord";
  const content = (msg.content || "").trim();
  const attachments = (msg.attachments || [])
    .map(a => a.url || a.filename)
    .filter(Boolean)
    .join("\n");
  const body = [content, attachments].filter(Boolean).join("\n").trim() || "(no text content)";
  const thread = route.name ? `#${route.name}` : "Discord thread";
  return `[${thread} · ${author}] ${body}`;
}
```

### Sync routing table from team charters
```typescript
export async function syncRouteTable(log: Log, _token: string, args: string[] = []) {
  const charters = teamCharterPaths(args);  // .maw/teams/*.yaml
  if (!charters.length) {
    log("✗ no team charters found in .maw/teams/*.yaml");
    return { ok: false, routes: 0 };
  }

  const agents = [...new Set(charters.flatMap(parseAgentsFromCharter))];
  const threads = await atlasThreadsList(args);  // maw atlas threads --json
  const target = routingPathForWrite(args);
  const existing = existsSync(target) ? loadRoutingTable(target) : {};
  const next: RoutingTable = {};
  const missing: string[] = [];

  for (const agent of agents) {
    const thread = findThreadForAgent(agent, threads);
    if (!thread) { missing.push(agent); continue; }
    next[thread.id] = {
      name: thread.name,
      pane: inferPane(agent, thread, existing, args),
      agent,
    };
  }

  if (!Object.keys(next).length) {
    log("✗ no agent threads matched; routing table not changed");
    if (!threads.length) log("  `maw atlas threads list --json` returned no threads");
    return { ok: false, routes: 0, missing };
  }

  writeJson(target, next);
  log(`✓ routing table synced: ${target}`);
  log(`  ${Object.keys(next).length} routes from ${agents.length} charter agents across ${charters.length} charter(s)`);
  for (const [threadId, route] of Object.entries(next)) {
    log(`  ${route.name || threadId} (${threadId}) → ${route.pane} [${route.agent || "agent"}]`);
  }
  if (missing.length) log(`  missing threads: ${missing.join(", ")}`);
  return { ok: true, routes: Object.keys(next).length, missing };
}
```

**Key pattern**: Routes run as background daemon, polling routing table every N seconds (default 5s), fetching new messages from each Discord thread, filtering bots/empty, forwarding via `maw hey <pane> <message>`. Routing table synced from team charters + thread discovery.

---

## 6. Spawn-Session — Tier 1 Orchestrator (`commands/spawn-session.ts`)

### Full session setup pipeline
```typescript
type Step = {
  label: string;
  argv: string[];
};

export async function spawnSession(log: Log, args: string[]) {
  const charter = args[1];
  if (!charter || charter === "help") {
    usage(log);
    return;
  }

  const dryRun = hasFlag(args, "--dry-run");
  const notifyTarget = hasFlag(args, "--no-notify") ? null : (argValue(args, "--notify") || DEFAULT_NOTIFY_TARGET);
  const steps: Step[] = [
    { label: "team up", argv: ["maw", "team", "up", charter] },
    { label: "team threads sync", argv: ["maw", "atlas", "team-threads", "sync"] },
    { label: "route start", argv: ["maw", "atlas", "route", "start"] },
  ];

  log(`maw atlas spawn-session ${charter}${dryRun ? " (dry-run)" : ""}`);
  for (const step of steps) {
    await runStep(step, dryRun, notifyTarget, log);
  }
  log("✓ spawn-session complete");
  await notify(notifyTarget, `[m5:atlas] spawn-session complete: ${charter}`, dryRun, log);
}
```

### Run single step with error handling
```typescript
async function runStep(step: Step, dryRun: boolean, notifyTarget: string | null, log: Log) {
  log(`→ ${step.label}: ${shellQuote(step.argv)}`);
  if (dryRun) {
    log(`dry-run: skipped ${step.label}`);
    await notify(notifyTarget, `[m5:atlas] spawn-session dry-run step ${step.label}: ${shellQuote(step.argv)}`, dryRun, log);
    return;
  }

  const result = await spawnText(step.argv);
  if (result.stdout.trim()) log(result.stdout.trim());
  if (result.stderr.trim()) log(result.stderr.trim());
  if (result.code !== 0) {
    await notify(notifyTarget, `[m5:atlas] spawn-session step failed: ${step.label} exited ${result.code}`, false, log);
    throw new Error(`${step.label} failed with exit code ${result.code}`);
  }

  log(`✓ ${step.label} complete`);
  await notify(notifyTarget, `[m5:atlas] spawn-session step complete: ${step.label}`, false, log);
}
```

**Key pattern**: Orchestrator runs 3 steps sequentially:
1. `maw team up <charter>` — spawn team tmux panes
2. `maw atlas team-threads sync` — create Discord threads for each agent
3. `maw atlas route start` — start daemon to forward thread messages to panes

Notifies main pane of progress after each step.

---

## 7. Reverse Bridge — Pane Output → Discord (`lib/reverse-bridge.ts`)

### Snapshot-based diff detection
```typescript
export type ReverseBridgeSnapshot = {
  panes: Record<string, string | undefined>;
  lastPostedAt?: Record<string, string | undefined>;
};

export async function runReverseBridgeOnce(
  log: Log,
  token: string,
  table: ReverseRouteTable,
  options: ReverseBridgeOptions = {},
): Promise<ReverseBridgeResult> {
  const snapshotFile = resolve(options.snapshotPath || DEFAULT_SNAPSHOT_FILE);
  const maxContentLength = options.maxContentLength || 1900;
  const snapshot = loadSnapshot(snapshotFile);
  let checked = 0;
  let changed = 0;
  let posted = 0;

  for (const [threadId, route] of Object.entries(table)) {
    checked++;
    const previous = snapshot.panes[route.pane];
    const current = await peekPane(route.pane);  // maw peek <pane>
    const diff = diffOutput(previous, current);
    snapshot.panes[route.pane] = current;

    if (!diff) continue;
    changed++;

    // First time seeing pane: seed snapshot, don't post
    if (!previous && !options.replayInitial) {
      log(`seeded: ${route.pane} → ${threadId} (initial snapshot, not posted)`);
      continue;
    }

    const content = formatDiscordContent(route, route.pane, diff, maxContentLength);
    if (options.dryRun) {
      log(`dry-run reverse post: ${route.pane} → ${threadId} (${content.length} chars)`);
    } else {
      await postMessage(token, threadId, content);
      snapshot.lastPostedAt![threadId] = new Date().toISOString();
      log(`reverse posted: ${route.pane} → ${threadId} (${content.length} chars)`);
    }
    posted++;
  }

  writeJson(snapshotFile, snapshot);
  return { checked, changed, posted };
}
```

### Peek pane and compute diff
```typescript
export async function peekPane(pane: string): Promise<string> {
  const bun = (globalThis as any).Bun;
  if (!bun?.spawn) return execPeekFallback(pane);

  const proc = bun.spawn(["maw", "peek", pane], {
    stdout: "pipe",
    stderr: "pipe",
  });
  const [code, stdout, stderr] = await Promise.all([
    proc.exited,
    streamToText(proc.stdout),
    streamToText(proc.stderr),
  ]);

  if (code !== 0) throw new Error([`maw peek ${pane} exited ${code}`, stderr].filter(Boolean).join("\n"));
  return stdout;
}

export function diffOutput(previous: string | undefined, current: string): string | null {
  if (previous === current) return null;
  if (!previous) return current.trim() || null;
  if (current.startsWith(previous)) return current.slice(previous.length).trim() || null;

  const prefix = commonPrefixLength(previous, current);
  const changed = current.slice(prefix).trim();
  return changed || current.trim() || null;
}
```

### Format for Discord (with truncation)
```typescript
function formatDiscordContent(route: ReverseRouteEntry, pane: string, diff: string, maxContentLength: number): string {
  const label = route.agent || route.name || pane;
  const header = `↩️ **${label}** (${pane}) output:`;
  const fenced = `${header}\n\`\`\`\n${diff}\n\`\`\``;
  if (fenced.length <= maxContentLength && fenced.length <= DISCORD_LIMIT) return fenced;
  return truncateDiscord(`${header}\n${diff}`, maxContentLength);
}

function truncateDiscord(content: string, maxContentLength: number): string {
  const max = Math.min(maxContentLength, DISCORD_LIMIT);
  if (content.length <= max) return content;
  const marker = `\n… truncated ${content.length - max} chars`;
  return content.slice(0, Math.max(0, max - marker.length)) + marker;
}
```

**Key pattern**: Polling peeks pane output, compares to previous snapshot, only posts if changed. First poll seeds snapshot without posting. Diffs are smart (append-only detection), truncated to Discord limits (2000 chars), formatted with labels and code fencing.

---

## 8. Watch Guards (`lib/watch-guards.ts`)

### allowFromGate — user whitelist check
```typescript
export type AllowFromInput = {
  userId?: string;
  channelId?: string;
  thread?: { id?: string; owner_id?: string; parent_id?: string };
  accessPath: string;
};

function allowedUsers(access: any, channelId?: string): Set<string> {
  const allow = new Set<string>();
  if (Array.isArray(access.allowFrom)) for (const id of access.allowFrom) allow.add(String(id));
  if (channelId && Array.isArray(access.groups?.[channelId]?.allowFrom)) {
    for (const id of access.groups[channelId].allowFrom) allow.add(String(id));
  }
  return allow;
}

export function allowFromGate(input: AllowFromInput): GuardDecision {
  const userId = input.userId || input.thread?.owner_id;
  if (!userId) return decision(false, "thread creator user ID missing");
  const access = readJson<any>(input.accessPath, {});
  const allowed = allowedUsers(access, input.channelId || input.thread?.parent_id);
  if (allowed.size === 0) return decision(false, "allowFrom is empty");
  return allowed.has(String(userId)) ? decision(true) : decision(false, `user ${userId} not in allowFrom`);
}
```

### maxWorktreesGate — capacity check
```typescript
export type MaxWorktreesInput = {
  activeWorkers?: number;
  maxWorktrees?: number;
  worktreeRoot?: string;
  state?: { spawned?: Record<string, unknown> };
};

function countWorktreeDirs(root: string): number {
  try {
    const agentsDir = resolve(root, "agents");
    return readdirSync(agentsDir, { withFileTypes: true })
      .filter(entry => entry.isDirectory())
      .filter(entry => /codex|atlas/i.test(entry.name))
      .length;
  } catch {
    return 0;
  }
}

export function maxWorktreesGate(input: MaxWorktreesInput = {}): GuardDecision {
  const max = input.maxWorktrees ?? 10;
  const stateCount = input.state?.spawned ? Object.keys(input.state.spawned).length : 0;
  const activeWorkers = input.activeWorkers ?? Math.max(stateCount, countWorktreeDirs(input.worktreeRoot || process.cwd()));
  if (activeWorkers >= max) return decision(false, `active workers ${activeWorkers} >= maxWorktrees ${max}`);
  return decision(true);
}
```

### Sanitization
```typescript
export function sanitizeThreadName(name: string, maxLength = 50): string {
  return sanitizeInput(name, maxLength) || "atlas-thread";
}

export function sanitizeBranchName(name: string): string {
  const safe = sanitizeThreadName(name, 50)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")  // Remove accents
    .replace(/[^a-z0-9._/-]+/g, "-")
    .replace(/\.\.+/g, ".")
    .replace(/^[-/.]+|[-/.]+$/g, "")
    .replace(/[-/]{2,}/g, "-")
    .slice(0, 50);
  return safe || `thread-${Date.now()}`;
}
```

### Cleanup — remove worktrees for archived threads
```typescript
export type CleanupRoute = {
  threadId: string;
  workerName?: string;
  pane?: string;
  worktreePath?: string;
};

export async function cleanupArchivedThreads(input: CleanupInput): Promise<CleanupResult> {
  const active = new Map(input.activeThreads.map(thread => [thread.id, thread]));
  const result: CleanupResult = { checked: input.routes.length, cleaned: 0, skipped: 0, errors: [] };
  const root = input.worktreeRoot || process.cwd();

  for (const route of input.routes) {
    const thread = active.get(route.threadId);
    const archived = !thread || thread.archived || thread.thread_metadata?.archived;
    if (!archived) { result.skipped++; continue; }

    try {
      const target = route.workerName || route.pane;
      if (target) {
        const kill = await execText(["maw", "kill", target], !!input.dryRun);
        if (kill.code !== 0) throw new Error(kill.stderr || kill.stdout || `maw kill ${target} failed`);
        input.log?.(`cleanup kill: ${target}`);
      }

      const worktree = routeWorktreePath(route, root);
      if (worktree && (input.dryRun || existsSync(worktree))) {
        const rm = await execText(["git", "worktree", "remove", "--force", worktree], !!input.dryRun);
        if (rm.code !== 0) throw new Error(rm.stderr || rm.stdout || `git worktree remove ${worktree} failed`);
        input.log?.(`cleanup worktree: ${basename(worktree)}`);
      }
      result.cleaned++;
    } catch (e) {
      result.errors.push({ route, error: e instanceof Error ? e.message : String(e) });
    }
  }

  return result;
}
```

**Key pattern**: Guards are pure functions that read config/state and return decisions. Cleanup is async and handles both `maw kill` and `git worktree remove --force` with error tracking.

---

## 9. Error Handling Patterns

### Watch guards integration
```typescript
async function allowFromGate(guards: WatchGuards, thread: ThreadInfo, channelId: string, args: string[]) {
  const file = accessPath(args);
  const fn = guards.allowFromGate || guards.checkAllowFrom;
  if (!fn) return fallbackAllowFrom(thread.owner_id, channelId, file);
  return gateOk(await fn({ userId: thread.owner_id, thread, channelId, accessPath: file }, thread.owner_id, channelId, file));
}

function gateOk(result: GuardResult): { ok: boolean; reason?: string; warning?: string } {
  if (typeof result === "boolean") return { ok: result };
  return {
    ok: result.ok ?? result.allowed ?? false,
    reason: result.reason,
    warning: result.warning,
  };
}
```

### Try-catch with logging in watch loop
```typescript
while (true) {
  try {
    const result = await watchOnce(log, token, channel, state, guards, args);
    log(`poll: ${result.active} active thread(s), ${result.newThreads} new`);
    if (result.newThreads) await notify(notifyTarget, `[m5:atlas] watch saw ${result.newThreads} new thread(s)...`, log);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    log(`watch error: ${msg}`);
    await notify(notifyTarget, `[m5:atlas] watch error in ${channel.name || channel.id}: ${msg}`, log);
  }

  if (hasFlag(args, "--once")) return;
  await sleep(intArg(args, "--interval", DEFAULT_INTERVAL_MS));
}
```

### Route daemon process management
```typescript
export async function stopRouteDaemon(log: Log, args: string[] = []) {
  const pidFile = pidPath(args);
  const pid = readPid(pidFile);
  if (!isProcessAlive(pid)) {
    try { unlinkSync(pidFile); } catch {}
    log("route daemon is not running");
    log(`  pid file: ${pidFile}`);
    return { ok: true, stopped: false };
  }

  process.kill(pid!, "SIGTERM");
  for (let i = 0; i < 20 && isProcessAlive(pid); i++) await sleep(100);
  if (isProcessAlive(pid) && args.includes("--force")) process.kill(pid!, "SIGKILL");
  if (isProcessAlive(pid)) {
    log(`✗ route daemon still running (pid ${pid}); retry with --force`);
    return { ok: false, stopped: false, pid };
  }

  try { unlinkSync(pidFile); } catch {}
  writeRuntimeStatus(args, { stoppedAt: new Date().toISOString(), pid: null });
  log(`✓ route daemon stopped (pid ${pid})`);
  return { ok: true, stopped: true, pid };
}
```

**Key pattern**: Errors logged with context (thread name, channel, reason), notifications sent to main pane, daemons gracefully shutdown with SIGTERM → SIGKILL escalation and PID tracking.

---

## 10. Utility Helpers

### Snowflake ID comparison (Discord message ordering)
```typescript
function snowflakeCompare(a: string, b: string): number {
  try {
    const aa = BigInt(a);
    const bb = BigInt(b);
    return aa < bb ? -1 : aa > bb ? 1 : 0;
  } catch {
    return a.localeCompare(b);
  }
}

function snowflakeToIso(id?: string): string {
  if (!id) return "never";
  try {
    const timestamp = Number((BigInt(id) >> 22n) + 1420070400000n);
    return new Date(timestamp).toISOString();
  } catch {
    return "unknown";
  }
}
```

### Arg parsing
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

### File I/O with atomic writes
```typescript
function readJson<T>(file: string, fallback: T): T {
  try { return JSON.parse(readFileSync(file, "utf8")); }
  catch { return fallback; }
}

function writeJson(file: string, value: any) {
  mkdirSync(dirname(file), { recursive: true });
  const tmp = `${file}.tmp-${process.pid}`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`);
  renameSync(tmp, file);  // Atomic on most POSIX systems
}
```

### Shell quoting
```typescript
function shellQuote(argv: string[]): string {
  return argv.map(a => /[^A-Za-z0-9_./:=@-]/.test(a) ? JSON.stringify(a) : a).join(" ");
}
```

---

## Summary of Key Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Thin dispatcher** | `index.ts` | Routes subcommands to command handlers |
| **REST client wrapper** | `lib/discord.ts` | Single `request()` method for all Discord API calls |
| **Snowflake comparison** | Throughout | Discord message ordering via BigInt compare |
| **State machine** | `watch.ts` | Tracks `knownThreads`, `pending`, `spawned` |
| **Confirmation gate** | `watch.ts` | Posts "spawn codex? reply go", waits for user confirmation |
| **Daemon supervisor** | `route.ts` | Spawns detached child, tracks PID, graceful SIGTERM/SIGKILL |
| **Polling poller** | `route.ts` | Infinite loop with configurable interval, forwards Discord → panes |
| **Snapshot diffing** | `reverse-bridge.ts` | Compares pane output to detect changes, only posts diffs |
| **Guard composition** | `watch-guards.ts` | Pure functions returning `{ ok, reason, warning }` |
| **Atomic writes** | Throughout | Atomic rename pattern to prevent corruption |
| **Argument parsing** | Throughout | Unified `argValue()`, `intArg()`, `hasFlag()` helpers |

