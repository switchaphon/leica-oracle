# MAW-JS Code Snippets & Architecture

**Date**: 2026-06-07  
**Source**: Soul-Brews-Studio/maw-js  
**Focus**: Multi-Agent Workflow CLI, Federation, Plugin System, Session Management

---

## 1. CLI Entry Point & Command Dispatch

### src/cli.ts (Main)

```typescript
#!/usr/bin/env bun
process.env.MAW_CLI = "1";

// #566: apply --as <name> BEFORE any state-touching import
import { applyInstancePreset } from "./cli/instance-preset";
applyInstancePreset();

import { logAudit } from "./core/fleet/audit";
import { usage } from "./cli/usage";
import { scanCommands } from "./cli/command-registry";
import { setVerbosityFlags } from "./cli/verbosity";
import { getVersionString } from "./cli/cmd-version";
import { runUpdate } from "./cli/cmd-update";
import { runBootstrap } from "./cli/plugin-bootstrap";
import { maybeAutoRestore } from "./cli/auto-restore";
import { dispatchCommand } from "./cli/dispatch";
import { handleTopLevelError } from "./cli/error-handler";
import { mawDataPath } from "./core/xdg";

const VERBOSITY_FLAGS = new Set(["--quiet", "-q", "--silent", "-s"]);
const rawArgs = process.argv.slice(2);
const verbosity: { quiet?: boolean; silent?: boolean } = {};
if (rawArgs.some(a => a === "--quiet" || a === "-q")) verbosity.quiet = true;
if (rawArgs.some(a => a === "--silent" || a === "-s")) verbosity.silent = true;
setVerbosityFlags(verbosity);
const args = rawArgs.filter(a => !VERBOSITY_FLAGS.has(a));
const cmd = args[0]?.toLowerCase();

async function main(): Promise<void> {
  if (cmd === "--version" || cmd === "-v" || cmd === "version") {
    console.log(getVersionString());
    return;
  }
  if (cmd === "update" || cmd === "upgrade") {
    await runUpdate(args);
    return;
  }

  const pluginDir = process.env.MAW_PLUGINS_DIR || mawDataPath("plugins");
  await runBootstrap(pluginDir, import.meta.dir);
  await scanCommands(pluginDir, "user");
  await maybeAutoRestore(cmd);

  if (!cmd || cmd === "--help" || cmd === "-h") {
    usage();
    return;
  }

  await dispatchCommand(cmd, args);
}

main().catch((e: unknown) => handleTopLevelError(e, args));
```

---

### src/cli/dispatch.ts (Command Router)

```typescript
/**
 * Run a command after plugins have been scanned. Walks the dispatch ladder:
 *   routeComm → routeTools → top-aliases → plugin registry (beta) →
 *   bundled plugin registry → agent-name shorthand.
 */

const CORE_ROUTES = [
  "hey", "send", "notify",
  "plugins", "plugin", "artifacts", "artifact",
  "agents", "agent", "audit", "serve",
  "update", "upgrade", "version",
];

export async function dispatchCommand(cmd: string, args: string[]): Promise<void> {
  const handled =
    (await routeComm(cmd, args)) ||
    (await routeTools(cmd, args));
  if (handled) return;

  const { resolveTopAlias, invokeDirectHandler } = await import("./top-aliases");
  const aliasResult = resolveTopAlias(args);
  if (aliasResult) {
    if (aliasResult.kind === "direct") {
      await invokeDirectHandler(aliasResult.handler, aliasResult.argv);
      return;
    }
    args.splice(0, args.length, ...aliasResult.argv);
  }

  const pluginMatch = matchCommand(args);
  if (pluginMatch) {
    await executeCommand(pluginMatch.desc, pluginMatch.remaining);
    return;
  }

  await dispatchPluginRegistry(cmd, args);
}

async function dispatchPluginRegistry(cmd: string, args: string[]): Promise<void> {
  const { discoverPackages, invokePlugin } = await import("../plugin/registry");
  const { resolvePluginMatch, validatePluginCliFlags } = await import("./dispatch-match");
  const plugins = discoverPackages();
  const cmdName = args.join(" ").toLowerCase();
  const dispatch = resolvePluginMatch(plugins, cmdName);

  if (dispatch.kind === "ambiguous") {
    console.error(`\x1b[31m✗\x1b[0m ambiguous command: ${args[0]}`);
    console.error(`  candidates: ${dispatch.candidates.map(c => `${c.plugin} (${c.name})`).join(", ")}`);
    throw new UserError(`ambiguous command: ${args[0]}`);
  }

  if (dispatch.kind === "match") {
    const matchedWords = dispatch.matchedName.split(/\s+/).filter(Boolean).length;
    const { dependencyStatus } = await import("../plugin/dependencies");
    const deps = dependencyStatus(dispatch.plugin, plugins);
    
    if (deps.missing.length > 0) {
      console.error(`\x1b[31m✗\x1b[0m '${dispatch.matchedName}' needs missing plugins: ${deps.missing.join(", ")}`);
      throw new UserError(`missing plugin dependency: ${dispatch.matchedName}`);
    }
    
    const remaining = args.slice(matchedWords);
    const flagValidation = validatePluginCliFlags(dispatch.plugin, remaining);
    if (!flagValidation.ok) {
      console.error(`\x1b[31m✗\x1b[0m unknown flag for ${dispatch.matchedName}: ${flagValidation.flag}`);
      throw new UserError(`unknown flag: ${flagValidation.flag}`);
    }

    const declared = (dispatch.plugin.manifest.cli?.flags ?? {}) as Record<string, any>;
    const { parsePluginFlags } = await import("./dispatch-flag-parse");
    const parsedFlags = parsePluginFlags(declared, remaining);
    
    const result = await invokePlugin(dispatch.plugin, {
      source: "cli",
      args: remaining,
      matchedName: dispatch.matchedName,
      ...(Object.keys(parsedFlags).length > 0 ? { flags: parsedFlags } : {}),
    });
    
    if (result.output) console.log(result.output);
    if (!result.ok) {
      if (result.error) console.error(result.error);
      process.exit(result.exitCode ?? 1);
    }
    process.exit(0);
  }
}
```

---

## 2. Session Management

### src/api/sessions.ts (API Routes)

```typescript
import { Elysia, t } from "elysia";
import { listSessions, capture, sendKeys } from "../core/transport/ssh";
import { checkPaneIdle } from "../commands/shared/comm-send";
import { findWindow } from "../core/runtime/find-window";
import { getAggregatedSessions, findPeerForTarget, sendKeysToPeer } from "../core/transport/peers";
import { loadConfig } from "../config";
import { resolveTarget, detectWindowMismatch } from "../core/routing";
import { processMirror } from "../lib/process-mirror";
import { cmdWake as defaultCmdWake, resolveFleetSession } from "../commands/shared/wake";
import { shouldAutoWake as defaultShouldAutoWake } from "../commands/shared/should-auto-wake";
import { cmdSleepOne as defaultCmdSleepOne } from "../lib/sleep";
import { WakeBody, SleepBody, SendBody } from "../lib/schemas";
import { Tmux } from "../core/transport/tmux";

export interface SessionsApiDeps {
  listSessions?: typeof listSessions;
  capture?: typeof capture;
  sendKeys?: typeof sendKeys;
  checkPaneIdle?: typeof checkPaneIdle;
  findWindow?: typeof findWindow;
  getAggregatedSessions?: typeof getAggregatedSessions;
  findPeerForTarget?: typeof findPeerForTarget;
  sendKeysToPeer?: typeof sendKeysToPeer;
  loadConfig?: typeof loadConfig;
  resolveTarget?: typeof resolveTarget;
  resolveFleetSession?: typeof resolveFleetSession;
  createTmux?: () => TmuxLike;
  shouldAutoWake?: (target: string, opts: AutoWakeOpts) => Promise<AutoWakeDecision>;
  cmdWake?: (target: string, opts: { noAttach: boolean; task?: string }) => Promise<unknown>;
  cmdSleepOne?: (target: string) => Promise<unknown>;
}

function defaults(deps: SessionsApiDeps) {
  return {
    listSessions: deps.listSessions ?? listSessions,
    capture: deps.capture ?? capture,
    sendKeys: deps.sendKeys ?? sendKeys,
    checkPaneIdle: deps.checkPaneIdle ?? checkPaneIdle,
    findWindow: deps.findWindow ?? findWindow,
    getAggregatedSessions: deps.getAggregatedSessions ?? getAggregatedSessions,
    findPeerForTarget: deps.findPeerForTarget ?? findPeerForTarget,
    sendKeysToPeer: deps.sendKeysToPeer ?? sendKeysToPeer,
    loadConfig: deps.loadConfig ?? loadConfig,
    resolveTarget: deps.resolveTarget ?? resolveTarget,
    resolveFleetSession: deps.resolveFleetSession ?? resolveFleetSession,
    createTmux: deps.createTmux ?? (() => new Tmux()),
    sleep: deps.sleep ?? ((ms: number) => Bun.sleep(ms)),
    shouldAutoWake: deps.shouldAutoWake ?? defaultShouldAutoWake,
    cmdWake: deps.cmdWake ?? defaultCmdWake,
    cmdSleepOne: deps.cmdSleepOne ?? defaultCmdSleepOne,
  };
}
```

---

### src/lib/sleep.ts (Graceful Sleep Flow)

```typescript
/**
 * Gracefully stop a single Oracle agent's tmux window:
 *   1. Send /exit to the Claude session
 *   2. Wait 3 seconds
 *   3. If window still exists, kill it
 *   4. Append a `sleep` event to the XDG data-primary maw-log.jsonl
 */

import { tmux, saveTabOrder } from "../sdk";
import { detectSession } from "../commands/shared/wake";
import { appendFile, mkdir } from "fs/promises";
import { runSleepLifecycleHooks } from "../plugin/lifecycle";
import { mawMessageLogPath } from "../core/xdg";

export async function cmdSleepOne(oracle: string, window?: string) {
  const session = await detectSession(oracle);
  if (!session) {
    throw new Error(`no running session found for '${oracle}'`);
  }

  const windowName = window ? `${oracle}-${window}` : `${oracle}-oracle`;

  await saveTabOrder(session);
  await runSleepLifecycleHooks({
    oracle,
    target: oracle,
    session,
    window: windowName,
  });

  let windows;
  try {
    windows = await tmux.listWindows(session);
  } catch {
    throw new Error(`could not list windows for session '${session}'`);
  }

  const stripDash = (s: string) => s.replace(/-+$/, "");
  const target = windows.find(w => 
    w.name === windowName || stripDash(w.name) === stripDash(windowName)
  );
  
  if (!target) {
    const fuzzy = windows.find(w =>
      stripDash(w.name) === stripDash(windowName) ||
      new RegExp(`^${oracle}-\\d+-${window}-?$`).test(w.name)
    );
    if (!fuzzy) {
      throw new Error(`window '${windowName}' not found in session '${session}'`);
    }
    return await doSleep(session, fuzzy.name, oracle);
  }

  await doSleep(session, windowName, oracle);
}

async function doSleep(session: string, windowName: string, oracle: string) {
  const target = `${session}:${windowName}`;

  console.log(`\x1b[90m...\x1b[0m sending /exit to ${target}`);
  try {
    for (const ch of "/exit") {
      await tmux.sendKeysLiteral(target, ch);
    }
    await tmux.sendKeys(target, "Enter");
  } catch {
    // Window might already be gone
  }

  await new Promise(r => setTimeout(r, 3000));

  try {
    const windows = await tmux.listWindows(session);
    const stripDash = (s: string) => s.replace(/-+$/, "");
    const stillExists = windows.some(w => 
      w.name === windowName || stripDash(w.name) === stripDash(windowName)
    );
    
    if (stillExists) {
      await tmux.killWindow(target);
      console.log(`  \x1b[33m!\x1b[0m force-killed ${windowName} (did not exit gracefully)`);
    } else {
      console.log(`  \x1b[32m✓\x1b[0m ${windowName} exited gracefully`);
    }
  } catch {
    console.log(`  \x1b[32m✓\x1b[0m ${windowName} stopped`);
  }

  const logFile = mawMessageLogPath();
  const line = JSON.stringify({
    ts: new Date().toISOString(),
    event: "sleep",
    oracle,
    window: windowName,
  });
  await appendFile(logFile, line + "\n");
}
```

---

## 3. Team Coordination

### src/api/teams.ts (Team API)

```typescript
import { Elysia } from "elysia";
import { readFileSync, readdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";
import { scanTeams } from "../engine/teams";

export interface TeamsApiDeps {
  scanTeams?: typeof scanTeams;
  readFileSync?: typeof readFileSync;
  readdirSync?: typeof readdirSync;
  join?: typeof join;
  homedir?: typeof homedir;
}

export function createTeamsApi(deps: TeamsApiDeps = {}) {
  const scan = deps.scanTeams ?? scanTeams;
  const readFile = deps.readFileSync ?? readFileSync;
  const readDir = deps.readdirSync ?? readdirSync;
  const joinPath = deps.join ?? join;
  const home = deps.homedir ?? homedir;

  const teamsApi = new Elysia();

  teamsApi.get("/teams", async () => {
    const teams = await scan();
    return { teams, total: teams.length };
  });

  teamsApi.get("/teams/:name", ({ params, set }) => {
    const configPath = joinPath(home(), ".claude/teams", params.name, "config.json");
    try { 
      return JSON.parse(readFile(configPath, "utf-8")); 
    } catch { 
      set.status = 404; 
      return { error: "team not found" }; 
    }
  });

  teamsApi.get("/teams/:name/tasks", ({ params }) => {
    const tasksDir = joinPath(home(), ".claude/tasks", params.name);
    try {
      const files = readDir(tasksDir).filter(f => f.endsWith(".json"));
      const tasks = files.map(f => {
        try { return JSON.parse(readFile(joinPath(tasksDir, f), "utf-8")); }
        catch { return null; }
      }).filter(Boolean);
      return { tasks, total: tasks.length };
    } catch { 
      return { tasks: [], total: 0 }; 
    }
  });

  return teamsApi;
}

export const teamsApi = createTeamsApi();
```

### src/engine/teams.ts (Team Liveness Check)

```typescript
import { readdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";
import { homedir } from "os";
import { tmux } from "../core/transport/tmux";

interface TeamMemberRuntime {
  name?: string;
  agentType?: string;
  backendType?: string;
  tmuxPaneId?: string;
  cwd?: string;
  joinedAt?: number;
}

interface TeamData {
  name: string;
  description: string;
  members: TeamMemberRuntime[];
  tasks: unknown[];
  alive: boolean;
}

const TEAMS_DIR = join(homedir(), ".claude/teams");
const TASKS_DIR = join(homedir(), ".claude/tasks");

async function livePaneIds(): Promise<Set<string>> {
  try {
    const raw = await tmux.run("list-panes", "-a", "-F", "#{pane_id}");
    return new Set(raw.split("\n").filter(Boolean));
  } catch { 
    return new Set(); 
  }
}

function isTeamAlive(members: TeamMemberRuntime[], panes: Set<string>): boolean {
  for (const m of members) {
    if (m.backendType === "tmux" && m.tmuxPaneId && panes.has(m.tmuxPaneId)) return true;
    if (m.backendType === "in-process" && m.cwd) {
      const isLocal = m.cwd.startsWith(homedir());
      if (!isLocal) continue;
      if (m.joinedAt && Date.now() - m.joinedAt < 2 * 60 * 60 * 1000) return true;
    }
  }
  return false;
}

export async function scanTeams(): Promise<TeamData[]> {
  try {
    const dirs = readdirSync(TEAMS_DIR).filter(d =>
      existsSync(join(TEAMS_DIR, d, "config.json"))
    );
    const panes = await livePaneIds();
    
    return dirs.map(d => {
      try {
        const config = JSON.parse(readFileSync(join(TEAMS_DIR, d, "config.json"), "utf-8"));
        const tasksDir = join(TASKS_DIR, d);
        let tasks: unknown[] = [];
        try {
          tasks = readdirSync(tasksDir)
            .filter(f => f.endsWith(".json"))
            .map(f => {
              try { return JSON.parse(readFileSync(join(tasksDir, f), "utf-8")); }
              catch { return null; }
            })
            .filter(Boolean);
        } catch { /* tasks dir may not exist */ }
        
        const alive = isTeamAlive(config.members || [], panes);
        return { ...config, tasks, alive };
      } catch { 
        return null; 
      }
    }).filter(Boolean) as TeamData[];
  } catch { 
    return []; 
  }
}

export async function broadcastTeams(clients: Set<MawWS>, lastJson: { value: string }): Promise<void> {
  if (clients.size === 0) return;
  const teams = await scanTeams();
  const json = JSON.stringify(teams);
  if (json === lastJson.value) return;
  lastJson.value = json;
  const msg = JSON.stringify({ type: "teams", teams });
  for (const ws of clients) ws.send(msg);
}
```

---

## 4. Fleet Management

### src/api/fleet.ts (Fleet Config API)

```typescript
import { Elysia } from "elysia";
import { readdirSync, readFileSync } from "fs";
import { join } from "path";
import { fleetDirForWrite, fleetDirsForRead, uniqueDirs } from "../core/fleet/paths";

export interface FleetApiDeps {
  fleetDir: string;
  fleetDirs?: string[];
  readdirSync: typeof readdirSync;
  readFileSync: typeof readFileSync;
  join: typeof join;
}

function defaultFleetApiDeps(): FleetApiDeps {
  return {
    fleetDir: fleetDirForWrite(),
    fleetDirs: fleetDirsForRead(),
    readdirSync,
    readFileSync,
    join,
  };
}

function readFleetConfigs(deps: FleetApiDeps): unknown[] {
  const dirs = uniqueDirs(deps.fleetDirs?.length ? deps.fleetDirs : [deps.fleetDir]);
  const seenFiles = new Set<string>();
  const configs: unknown[] = [];
  let sawReadableDir = false;
  let lastError: unknown = null;

  for (const dir of dirs) {
    let files: string[];
    try {
      files = deps.readdirSync(dir)
        .filter(f => f.endsWith(".json") && !f.endsWith(".disabled"))
        .sort();
      sawReadableDir = true;
    } catch (e) {
      lastError = e;
      continue;
    }

    for (const file of files) {
      if (seenFiles.has(file)) continue;
      seenFiles.add(file);
      configs.push(JSON.parse(
        deps.readFileSync(deps.join(dir, file), "utf-8") as string
      ));
    }
  }

  if (!sawReadableDir && lastError) throw lastError;
  return configs;
}

export function createFleetApi(deps: FleetApiDeps = defaultFleetApiDeps()) {
  const api = new Elysia();

  // PUBLIC FEDERATION API (v1) — no auth. Shape is load-bearing for lens
  // clients that compute lineage by inverting `budded_from`.
  api.get("/fleet-config", () => {
    try {
      return { configs: readFleetConfigs(deps) };
    } catch (e: any) {
      return { configs: [], error: e.message };
    }
  });

  return api;
}

export const fleetApi = createFleetApi();
```

---

## 5. Federation & Peer Discovery

### src/api/federation.ts (Federation API)

```typescript
import { Elysia, t } from "elysia";
import { getFederationStatus } from "../core/transport/peers";
import { loadConfig } from "../config";
import { listSnapshots, loadSnapshot } from "../core/fleet/snapshot";
import { hostedAgents as defaultHostedAgents } from "../commands/shared/federation-sync";
import { getPeerKey } from "../lib/peer-key";
import { resolveNodeIdentity } from "../core/fleet/node-identity";
import { mawMessageLogCandidatePaths } from "../core/xdg";

const ADVERTISED_ENDPOINTS: string[] = [
  "/api/identity",
  "/api/messages",
  "/api/pane-keys",
  "/api/probe",
  "/api/send",
  "/api/sleep",
  "/api/wake",
];

export { defaultHostedAgents as hostedAgents };

export interface FederationApiDeps {
  getFederationStatus?: typeof getFederationStatus;
  listSnapshots?: typeof listSnapshots;
  loadSnapshot?: typeof loadSnapshot;
  loadConfig?: typeof loadConfig;
  hostedAgents?: typeof defaultHostedAgents;
  getPeerKey?: typeof getPeerKey;
  packageVersion?: string;
  uptime?: () => number;
  nowIso?: () => string;
  readFileSync?: typeof readFileSync;
  readdirSync?: typeof readdirSync;
  messageLogPaths?: () => string[];
}

export function createFederationApi(deps: FederationApiDeps = {}) {
  const federationStatus = deps.getFederationStatus ?? getFederationStatus;
  const snapshots = deps.listSnapshots ?? listSnapshots;
  const snapshot = deps.loadSnapshot ?? loadSnapshot;
  const load = deps.loadConfig ?? loadConfig;
  const agentsForHost = deps.hostedAgents ?? defaultHostedAgents;
  const peerKey = deps.getPeerKey ?? getPeerKey;
  const version = deps.packageVersion ?? require("../../package.json").version;
  const uptime = deps.uptime ?? (() => process.uptime());
  const nowIso = deps.nowIso ?? (() => new Date().toISOString());
  
  const api = new Elysia();
  
  // Routes...
  return api;
}
```

### src/core/transport/peers.ts (Peer Reachability)

```typescript
/**
 * Check if a peer is reachable by making a GET /api/sessions request.
 * ONE-WAY ONLY: verifies local→peer reach, NOT peer→local.
 */

import { loadConfig, cfgTimeout, cfgLimit, cfgInterval } from "../../config";
import type { Session } from "./ssh";
import { curlFetch } from "./curl-fetch";

function isValidPeerSession(item: unknown): item is Session {
  if (!item || typeof item !== "object") return false;
  const s = item as Record<string, unknown>;
  return (
    typeof s.name === "string" &&
    /^[a-zA-Z0-9_.\-]+$/.test(s.name) &&
    Array.isArray(s.windows)
  );
}

let aggregatedCache: { peers: (Session & { source?: string })[]; ts: number } | null = null;
const CACHE_TTL = 30_000;

export interface PeerStatus {
  url: string;
  peerName?: string;
  reachable: boolean;
  latency?: number;
  node?: string;
  agents?: string[];
  clockDeltaMs?: number;
  clockWarning?: boolean;
}

const CLOCK_WARN_MS = 3 * 60 * 1000; // 3 minutes

/**
 * #1975: Probe `GET /api/sessions` with retries to absorb transient WG jitter.
 */
async function probeSessionsWithRetry(url: string) {
  const retries = Math.max(0, cfgLimit("peerProbeRetries"));
  const backoff = Math.max(0, cfgInterval("peerRetryBackoff"));
  let lastErr: unknown;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    if (attempt > 0 && backoff > 0) await Bun.sleep(backoff);
    try {
      const res = await curlFetch(`${url}/api/sessions`, { timeout: cfgTimeout("http") });
      if (res.ok || attempt === retries) return res;
    } catch (err) {
      lastErr = err;
      if (attempt === retries) throw err;
    }
  }
  throw lastErr ?? new Error(`peer probe failed: ${url}`);
}

async function checkPeerReachable(url: string): Promise<{
  reachable: boolean; 
  latency: number; 
  node?: string; 
  agents?: string[]; 
  clockDeltaMs?: number;
}> {
  const start = Date.now();
  try {
    const res = await probeSessionsWithRetry(url);
    const latency = Date.now() - start;
    if (!res.ok) return { reachable: false, latency };
    
    const body = await res.json();
    const sessions = (body.sessions || [])
      .filter(isValidPeerSession)
      .map((s: Session) => ({ ...s, source: "peer" }));
    
    return { 
      reachable: true, 
      latency,
      agents: sessions.flatMap((s: any) => s.windows.map(w => `${s.name}:${w.name}`)),
    };
  } catch (err) {
    return { reachable: false, latency: Date.now() - start };
  }
}
```

---

## 6. Federation Authentication

### src/lib/federation-auth.ts (HMAC Signing)

```typescript
/**
 * Federation Auth — HMAC-SHA256 request signing for peer-to-peer trust.
 *
 * Design:
 *   - Each node shares a `federationToken` (config field, min 16 chars)
 *   - Outgoing HTTP calls sign: HMAC-SHA256(token, "METHOD:PATH:TIMESTAMP[:BODY_SHA256]")
 *   - Incoming requests verify signature within ±5 min window
 *   - No token configured → all requests pass (backwards compat)
 *   - Loopback requests always pass (local CLI / browser)
 *
 * Signature versions:
 *   - v1 (legacy): METHOD:PATH:TIMESTAMP (body NOT signed)
 *   - v2 (preferred): METHOD:PATH:TIMESTAMP:BODY_SHA256 (body-bound)
 *   - v3 (from-signing): METHOD:PATH:TIMESTAMP:BODY_SHA256:FROM (ed25519 per-peer)
 */

import { createHash, createHmac, timingSafeEqual } from "crypto";
import { loadConfig } from "../config";

const WINDOW_SEC = 300; // ±5 minutes

export function hashBody(body: string | Uint8Array | undefined | null): string {
  if (body == null || (typeof body === "string" && body.length === 0)) return "";
  if (body instanceof Uint8Array && body.length === 0) return "";
  return createHash("sha256").update(body as string | Buffer).digest("hex");
}

const PROTECTED = new Set([
  "/api/send",
  "/api/pane-keys",
  "/api/talk",
  "/api/transport/send",
  "/api/triggers/fire",
  "/api/worktrees/cleanup",
]);

const PROTECTED_POST = new Set([
  "/api/feed",
]);

/**
 * Sign a request. When `bodyHash` is provided, produces a v2 signature that
 * binds the signature to the body bytes. When omitted, produces a v1 signature.
 */
export function sign(
  token: string, 
  method: string, 
  path: string, 
  timestamp: number, 
  bodyHash = ""
): string {
  const payload = bodyHash
    ? `${method}:${path}:${timestamp}:${bodyHash}`
    : `${method}:${path}:${timestamp}`;
  return createHmac("sha256", token).update(payload).digest("hex");
}

/**
 * Verify a signature. `bodyHash` must match what was signed.
 */
export function verify(
  token: string, 
  method: string, 
  path: string, 
  timestamp: number, 
  signature: string, 
  bodyHash = ""
): boolean {
  const now = Math.floor(Date.now() / 1000);
  const delta = Math.abs(now - timestamp);
  if (delta > WINDOW_SEC) return false;

  const expected = sign(token, method, path, timestamp, bodyHash);
  if (expected.length !== signature.length) return false;

  try {
    return timingSafeEqual(
      Buffer.from(expected, "hex"), 
      Buffer.from(signature, "hex")
    );
  } catch {
    return false;
  }
}

export function isLoopback(address: string | undefined): boolean {
  if (!address) return false;
  return address === "127.0.0.1"
    || address === "::1"
    || address === "::ffff:127.0.0.1"
    || address === "localhost"
    || address.startsWith("127.");
}

export function signHeaders(
  token: string,
  method: string,
  path: string,
  body?: string | Uint8Array
): Record<string, string> {
  const timestamp = Math.floor(Date.now() / 1000);
  const bodyHash = hashBody(body);
  const signature = sign(token, method, path, timestamp, bodyHash);
  
  return {
    "X-Maw-Timestamp": timestamp.toString(),
    "X-Maw-Signature": signature,
    ...(bodyHash ? { "X-Maw-Auth-Version": "v2" } : {}),
  };
}
```

### src/lib/elysia-auth.ts (Elysia Auth Plugin)

```typescript
/**
 * Federation Auth — Elysia plugin (replaces Hono middleware)
 * HMAC-SHA256 request signing for peer-to-peer trust.
 */

import { Elysia } from "elysia";
import { loadConfig, D } from "../config";
import { verify, isLoopback, verifyRequest } from "./federation-auth";
import { loadPeers } from "./peers/store";
import type { Server } from "bun";

const WINDOW_SEC = D.hmacWindowSeconds;

const PROTECTED = new Set([
  "/send",
  "/pane-keys",
  "/probe",
  "/wake",
  "/sleep",
  "/talk",
  "/transport/send",
  "/triggers/fire",
  "/worktrees/cleanup",
  "/_engine/register",
  "/_engine/unregister",
]);

const PROTECTED_POST = new Set([
  "/feed",
]);

export function isProtected(path: string, method: string): boolean {
  if (PROTECTED.has(path)) return true;
  if (PROTECTED_POST.has(path) && method === "POST") return true;
  if (method === "POST" && path.startsWith("/plugins/")) return true;
  if (method === "GET" && path.startsWith("/plugin/download/")) return true;
  return false;
}

let _bunServer: Server | null = null;

export function setBunServer(server: Server): void {
  _bunServer = server;
}

const rawBodyBytes = new WeakMap<Request, Uint8Array>();
const BODY_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const textDecoder = new TextDecoder();

function jsonLike(contentType: string): boolean {
  return contentType === "application/json" || contentType.endsWith("+json");
}

async function captureBodyForAuth(
  request: Request, 
  contentType: string
): Promise<unknown> {
  const config = loadConfig();
  if (!config.federationToken) return undefined;

  if (!BODY_METHODS.has(request.method)) return undefined;
  
  const bytes = new Uint8Array(await request.arrayBuffer());
  rawBodyBytes.set(request, bytes);
  
  const normalized = contentType.split(";", 1)[0]?.trim().toLowerCase() ?? "";
  if (jsonLike(normalized)) {
    const text = textDecoder.decode(bytes);
    return text.trim() ? JSON.parse(text) : null;
  }
  if (normalized === "text/plain") {
    return textDecoder.decode(bytes);
  }
  if (normalized === "application/x-www-form-urlencoded") {
    return Object.fromEntries(
      new URLSearchParams(textDecoder.decode(bytes))
    );
  }
  if (normalized === "application/octet-stream") {
    return bytes;
  }
  return undefined;
}
```

---

## 7. Plugin System

### src/plugin/registry.ts (Plugin Discovery & Registry)

```typescript
/**
 * Plugin registry — discover plugin packages and invoke them.
 *
 * Scans ~/.maw/plugins/<name>/plugin.json
 *
 * Phase A gates (enforced at load time):
 *  1. Semver gate — `manifest.sdk` must satisfy runtime SDK version
 *  2. Artifact hash — if `manifest.artifact.sha256` is set, on-disk bundle
 *     must match (skip for symlink/dev-mode installs)
 *  3. Dev-mode detection — symlink installs skip hash verification
 *  4. Legacy manifests (no artifact field) still load with warning
 */

import { existsSync, readFileSync, readdirSync, realpathSync } from "fs";
import { join, resolve, sep } from "path";
import { pathToFileURL } from "url";
import { loadManifestFromDir } from "./manifest";
import { loadConfig } from "../config";
import { verbose, info, warn } from "../cli/verbosity";
import type { MawConfig } from "../config/types";
import type { LoadedPlugin } from "./types";
import { satisfies, formatSdkMismatchError } from "./registry-semver";
import {
  runtimeSdkVersion,
  scanDirs,
  hashFile,
  isDevModeInstall,
  warnLegacyOnce,
} from "./registry-helpers";

export { satisfies, formatSdkMismatchError } from "./registry-semver";
export { runtimeSdkVersion, hashFile, isDevModeInstall } from "./registry-helpers";
export { invokePlugin } from "./registry-invoke";

let _discoverCache: LoadedPlugin[] | null = null;
const _moduleSymbolCache = new Map<string, unknown>();

export function resetDiscoverCache(): void {
  _discoverCache = null;
  _moduleSymbolCache.clear();
}

function resolvePluginModulePath(plugin: LoadedPlugin): string {
  const modulePath = plugin.manifest.module?.path;
  if (!modulePath) throw new Error(
    `plugin '${plugin.manifest.name}' does not declare module.path`
  );
  
  const resolved = resolve(plugin.dir, modulePath);
  const pluginRoot = realpathSync(plugin.dir);
  const realPath = realpathSync(resolved);
  
  if (realPath !== pluginRoot && !realPath.startsWith(pluginRoot + sep)) {
    throw new Error(
      `plugin '${plugin.manifest.name}' module.path escapes plugin dir: ${modulePath}`
    );
  }
  
  return realPath;
}

/**
 * Import a whitelisted named symbol from another plugin's module surface.
 * Plugins opt in via plugin.json:
 *   { "module": { "path": "./lib.ts", "exports": ["helper"] } }
 */
export interface ImportPluginSymbolDeps {
  discoverPackages?: () => LoadedPlugin[];
}
```

### packages/sdk/plugin.ts (Plugin SDK)

```typescript
/**
 * @maw-js/sdk/plugin — plugin-authoring surface.
 *
 * Single import line for plugin authors:
 *
 *   import {
 *     type InvokeContext,
 *     type InvokeResult,
 *     UserError,
 *     isUserError,
 *     parseFlags,
 *   } from "@maw-js/sdk/plugin";
 *
 *   export default async function (ctx: InvokeContext): Promise<InvokeResult> {
 *     if (!ctx.args) throw new UserError("missing args");
 *     return { ok: true, output: "hello" };
 *   }
 */

export type { InvokeContext, InvokeResult } from "../../src/plugin/types";
export { UserError, isUserError } from "../../src/core/util/user-error";
export { parseFlags } from "../../src/cli/parse-args";
```

### src/api/plugins.ts (Plugin HTTP API)

```typescript
/**
 * Plugins API — HTTP surface for package-based plugins (plugin.json manifest).
 *
 * Routes (mounted under /api):
 *   GET  /plugins          → list plugins that expose an API surface
 *   GET  /plugins/:name    → invoke plugin via GET (query params as args)
 *   POST /plugins/:name    → invoke plugin via POST (body as args)
 *
 * Auth: POST routes are guarded by HMAC middleware
 * (see isProtected — /plugins/ prefix is protected for POST).
 */

import { Elysia, t } from "elysia";
import type { LoadedPlugin, InvokeContext, InvokeResult } from "../plugin/types";
import { discoverPackages, invokePlugin } from "../plugin/registry";

export interface PluginsRouterDeps {
  discoverPackages: typeof discoverPackages;
  invokePlugin: typeof invokePlugin;
}

export function createPluginsRouter(deps: PluginsRouterDeps = {
  discoverPackages,
  invokePlugin,
}) {
  const router = new Elysia();

  router.get("/plugins", () => {
    const all = deps.discoverPackages();
    return all
      .filter((p: LoadedPlugin) => !!p.manifest.api)
      .map((p: LoadedPlugin) => ({
        name: p.manifest.name,
        version: p.manifest.version,
        api: p.manifest.api,
      }));
  });

  router.get("/plugins/:name", async ({ params, query, set }) => {
    const all = deps.discoverPackages();
    const plugin: LoadedPlugin | undefined = all.find(
      (p: LoadedPlugin) => p.manifest.name === params.name
    );

    if (!plugin) {
      set.status = 404;
      return { ok: false, error: `plugin '${params.name}' not found` };
    }
    if (!plugin.manifest.api?.methods.includes("GET")) {
      set.status = 405;
      return { ok: false, error: "method not allowed" };
    }

    const result: InvokeResult = await deps.invokePlugin(plugin, {
      source: "api",
      args: query as Record<string, unknown>,
    } satisfies InvokeContext);

    if (!result.ok) {
      set.status = 500;
      return { ok: false, error: result.error ?? "invoke failed" };
    }
    return { ok: true, output: result.output };
  });

  router.post("/plugins/:name", async ({ params, body, set }) => {
    const all = deps.discoverPackages();
    const plugin: LoadedPlugin | undefined = all.find(
      (p: LoadedPlugin) => p.manifest.name === params.name
    );

    if (!plugin) {
      set.status = 404;
      return { ok: false, error: `plugin '${params.name}' not found` };
    }
    if (!plugin.manifest.api?.methods.includes("POST")) {
      set.status = 405;
      return { ok: false, error: "method not allowed" };
    }

    const result: InvokeResult = await deps.invokePlugin(plugin, {
      source: "api",
      args: body,
    } satisfies InvokeContext);

    if (!result.ok) {
      set.status = 500;
      return { ok: false, error: result.error ?? "invoke failed" };
    }
    return { ok: true, output: result.output };
  });

  return router;
}

export const pluginsApi = createPluginsRouter();
```

---

## 8. Routing & Target Resolution

### src/core/routing.ts (Target Resolution)

```typescript
/**
 * Shared routing resolver — unifies cmdSend (client) and /api/send (server).
 *
 * Resolution order:
 *   1. Local findWindow → { type: 'local' }
 *   2. Node:prefix → namedPeers → { type: 'peer' } or { type: 'self-node' }
 *   3. Manifest entry → peer URL → { type: 'peer' }
 *   4. Agents map → peer URL → { type: 'peer' }
 *   5. Peer alias → peers.json node/identity → { type: 'peer' }
 *   6. null (caller handles peer discovery fallback)
 */

import { findWindow, type Session } from "./runtime/find-window";
import type { MawConfig } from "../config";
import { resolveFleetSession } from "../commands/shared/fleet-load";
import { loadManifestCached, type OracleManifestEntry } from "../lib/oracle-manifest";
import { loadPeers, type Peer } from "../lib/peers/store";

export type { Session };

export type ResolveResult =
  | { type: "local"; target: string }
  | { type: "peer"; peerUrl: string; target: string; node: string }
  | { type: "self-node"; target: string }
  | { type: "error"; reason: string; detail: string; hint?: string }
  | null;

/**
 * Resolve a query to a local target, remote peer, or null.
 * Sync and read-only — no network calls. Testable without mocks.
 */
export function resolveTarget(
  query: string,
  config: MawConfig,
  sessions: (Session & { source?: string })[],
  currentSession?: string,
): ResolveResult {
  if (!query) return {
    type: "error",
    reason: "empty_query",
    detail: "no target specified",
    hint: "usage: maw hey <agent> <message>",
  };

  const writable = sessions.filter(s =>
    !s.name.endsWith("-view") &&
    (s.source === undefined || s.source === "local"),
  );

  const selfNode = config.node ?? "local";

  // Exact tmux address (session:window:pane)
  const exactTmuxAddress = resolveExactTmuxPaneAddress(query, writable, "local");
  if (exactTmuxAddress) return exactTmuxAddress;

  // Fleet config: oracle name → session name → findWindow
  const fleetSession = resolveFleetSession(query) || 
    resolveFleetSession(query.replace(/-oracle$/, ""));
  if (fleetSession) {
    const fleetResult = resolveFleetWindowTarget(fleetSession, query, writable, "local");
    if (fleetResult) return fleetResult;
  }

  // Session alias window convention (prefer <oracle>-oracle window)
  if (!query.includes(":")) {
    const sessionAliasResult = resolveSessionAliasWindowTarget(query, writable, "local");
    if (sessionAliasResult) return sessionAliasResult;
  }

  // Local findWindow
  const localTarget = findWindow(writable, query, currentSession);
  if (localTarget) {
    return { type: "local", target: localTarget };
  }

  // Node:agent syntax
  if (query.includes(":")) {
    const [nodeName, agentName] = query.split(":", 2);
    if (nodeName === selfNode) {
      return { type: "self-node", target: agentName };
    }
    const namedPeers = config.peers?.filter(p => p.node === nodeName);
    if (namedPeers?.length === 1) {
      return { type: "peer", peerUrl: namedPeers[0].url, target: agentName, node: nodeName };
    }
  }

  // Manifest lookup (30s TTL)
  try {
    const manifest = loadManifestCached();
    const entry = manifest?.agents?.find(a => a.name === query);
    if (entry && entry.node !== selfNode) {
      const namedPeer = config.peers?.find(p => p.node === entry.node);
      if (namedPeer) {
        return { 
          type: "peer", 
          peerUrl: namedPeer.url, 
          target: entry.name, 
          node: entry.node 
        };
      }
    }
  } catch {
    // Swallow manifest load failures
  }

  // Agents map fallback
  const agents = config.agents || {};
  const agentUrl = agents[query];
  if (agentUrl) {
    const peer = (config.peers || []).find(p => p.url === agentUrl);
    return {
      type: "peer",
      peerUrl: agentUrl,
      target: query,
      node: peer?.node || "unknown",
    };
  }

  // Peer alias
  const peers = loadPeers();
  const aliasPeer = peers.find(p => 
    p.name === query || p.identity === query
  );
  if (aliasPeer) {
    return {
      type: "peer",
      peerUrl: aliasPeer.url,
      target: query,
      node: aliasPeer.node || "unknown",
    };
  }

  return null;
}
```

---

## 9. Transport Layer

### src/core/transport/tmux.ts (Tmux Abstraction)

```typescript
/**
 * Barrel re-export. The tmux abstraction is split across:
 *   tmux-types.ts      — types + q() + resolveSocket() + tmuxCmd()
 *   tmux-class.ts      — Tmux class + default `tmux` instance
 *   tmux-pane-lock.ts  — withPaneLock + splitWindowLocked
 *   tmux-pane-tags.ts  — tagPane + readPaneTags
 */

export type { TmuxPane, TmuxWindow, TmuxSession } from "./tmux-types";
export { resolveSocket, tmuxCmd } from "./tmux-types";
export { Tmux, tmux } from "./tmux-class";
export type { SplitWindowLockedOpts } from "./tmux-pane-lock";
export { withPaneLock, splitWindowLocked } from "./tmux-pane-lock";
export type { TagPaneOpts, PaneTags } from "./tmux-pane-tags";
export { tagPane, readPaneTags } from "./tmux-pane-tags";
```

---

## 10. API Server & Proxy

### src/api/proxy.ts (HTTP Proxy Barrel)

```typescript
/**
 * POST /api/proxy — generic HTTP proxy for REST access to HTTP-LAN peers.
 * Barrel re-export — implementation split across proxy-*.ts siblings.
 */

export { proxyApi } from "./proxy-routes";
export { parseProxySignature } from "./proxy-auth";
export { isReadOnlyMethod, isKnownMethod, isPathProxyable, isProxyShellPeerAllowed } from "./proxy-trust";
export { resolveProxyPeerUrl } from "./proxy-relay";
```

---

## Key Patterns & Design Notes

### 1. Dependency Injection

All API modules use a `Deps` interface pattern:
```typescript
export interface SessionsApiDeps {
  listSessions?: typeof listSessions;
  // ...optional overrides
}

function defaults(deps: SessionsApiDeps) {
  return { 
    listSessions: deps.listSessions ?? listSessions,
    // ... use defaults if not provided
  };
}
```

### 2. Dispatch Hierarchy

```
routeComm → routeTools → top-aliases → plugin registry → 
  plugin dependencies → bundled commands → error handling
```

### 3. Federation Auth Layers

- **v1**: METHOD:PATH:TIMESTAMP (body unsigned — legacy)
- **v2**: METHOD:PATH:TIMESTAMP:BODY_SHA256 (body-bound, preferred)
- **v3**: v2 + FROM:PUBKEY signing (ed25519 per-peer, #804 Step 4)

### 4. Protected Routes (Auth Required)

```
/api/send, /api/pane-keys, /api/probe, /api/wake, /api/sleep, 
/api/talk, /api/triggers/fire, /api/worktrees/cleanup,
POST /plugins/*, GET /plugin/download/*
```

### 5. Session Scope

- **Local sessions**: writable panes on this node (exclude -view mirrors)
- **Federated sessions**: immutable mirrors from other peers (source:"peer")
- **Fleet resolution**: manifest → oracles.json → agents map

### 6. Team Liveness

Checks tmux pane existence + in-process cwd locality + recency (< 2h).

### 7. Plugin Discovery

- Scans `~/.maw/plugins/<name>/plugin.json`
- Enforces Semver gate on manifest.sdk
- Verifies artifact.sha256 (skip for symlink/dev installs)
- Lazy caches result per CLI invocation (not per session)

### 8. Error Handling

- User-facing: `UserError` (thrown, caught at CLI level)
- Transport: `401` (HMAC fail), `404` (not found), `405` (method not allowed)
- Plugin: flags validation before invocation

