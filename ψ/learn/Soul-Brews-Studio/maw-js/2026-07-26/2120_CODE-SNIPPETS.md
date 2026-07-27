# maw-js Code Snippets — 2026-07-26

## Overview

This document collects representative code from **maw-js v26.6.14-alpha.2110** (alpha branch), focusing on:
- CLI entry point and command dispatch
- tmux integration and send-keys reliability  
- messaging and routing layer  
- agent spawn path (`maw workon`)
- error handling idioms
- testing approach

**Target audience**: Developers integrating with maw-js, understanding the transport layer, debugging tmux send-keys issues.

---

## 1. CLI Entry Point & Command Dispatch

### Entry Point: `src/cli.ts`

The CLI boot sequence handles version flags, plugin bootstrap, and command dispatch:

```typescript
#!/usr/bin/env bun
process.env.MAW_CLI = "1";

// #566: apply --as <name> BEFORE any state-touching import (paths.ts evaluates
// MAW_HOME at module load). Must be the first side effect.
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

// Strip verbosity flags up-front so they don't collide with cmd detection or
// leak into plugin argv. Task #3 will flip call sites to honor these.
const VERBOSITY_FLAGS = new Set(["--quiet", "-q", "--silent", "-s"]);
const rawArgs = process.argv.slice(2);
const verbosity: { quiet?: boolean; silent?: boolean } = {};
if (rawArgs.some(a => a === "--quiet" || a === "-q")) verbosity.quiet = true;
if (rawArgs.some(a => a === "--silent" || a === "-s")) verbosity.silent = true;
setVerbosityFlags(verbosity);
const args = rawArgs.filter(a => !VERBOSITY_FLAGS.has(a));
const cmd = args[0]?.toLowerCase();

logAudit(cmd || "", args);

async function main(): Promise<void> {
  if (cmd === "--version" || cmd === "-v" || cmd === "version") {
    console.log(getVersionString());
    return;
  }
  if (cmd === "update" || cmd === "upgrade") {
    await runUpdate(args);
    return;
  }

  // Auto-bootstrap: if the XDG data plugin dir is empty, symlink bundled +
  // install from pluginSources.
  const pluginDir = process.env.MAW_PLUGINS_DIR || mawDataPath("plugins");
  await runBootstrap(pluginDir, import.meta.dir);

  // Load plugins from the resolved data plugin dir — the single source of truth.
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

**Key observations**:
- **Instance preset** applied first, before any module load that depends on MAW_HOME
- **Plugin bootstrap** auto-symlinks bundled plugins on first run
- **Command audit** logged for analytics
- **Error handling** deferred to top-level handler (only prints UserError; lets stack show for unexpected failures)

### Command Dispatch: `src/cli/dispatch.ts`

The dispatch ladder resolves commands in priority order:

```typescript
/**
 * Run a command after plugins have been scanned. Walks the dispatch ladder:
 *   routeComm → routeTools → top-aliases → plugin registry (beta) →
 *   bundled plugin registry → agent-name shorthand.
 */
export async function dispatchCommand(cmd: string, args: string[]): Promise<void> {
  const handled =
    (await routeComm(cmd, args)) ||
    (await routeTools(cmd, args));
  if (handled) return;

  // RFC #954 — top-level verb aliases. Sits between routeTools and
  // matchCommand. Either rewrites argv in place (continue dispatch flow)
  // or dispatches a direct-handler and exits the pipeline.
  const { resolveTopAlias, invokeDirectHandler } = await import("./top-aliases");
  const aliasResult = resolveTopAlias(args);
  if (aliasResult) {
    if (aliasResult.kind === "direct") {
      await invokeDirectHandler(aliasResult.handler, aliasResult.argv);
      return;
    }
    args.splice(0, args.length, ...aliasResult.argv);
  }

  // Try plugin commands (beta) — after core routes, before fallback
  const pluginMatch = matchCommand(args);
  if (pluginMatch) {
    await executeCommand(pluginMatch.desc, pluginMatch.remaining);
    return;
  }

  // Fallback: check plugin registry for bundled commands
  await dispatchPluginRegistry(cmd, args);
}
```

**The ladder** (in order):
1. **routeComm** — `maw hey`, `maw send`, `maw notify` (agent messaging)
2. **routeTools** — `maw peek`, `maw ls`, `maw status` (local state queries)
3. **top-aliases** — verb rewrites (e.g., `up` → `workon`)
4. **plugin registry** — dynamic commands from installed plugins
5. **bundled plugins** — fallback to vendor plugins  
6. **unknown command** — fuzzy suggestions

**File**: `src/cli/dispatch.ts:25-53` | **Lines**: 25–53

---

## 2. tmux Integration & send-keys Reliability

### Send-Keys Base Implementation: `src/core/transport/tmux-class.ts`

The low-level `sendKeys` method maps to tmux's native send-keys command:

```typescript
async sendKeys(target: string, ...keys: string[]): Promise<void> {
  await this.run("send-keys", "-t", target, ...keys);
}

async sendKeysLiteral(target: string, text: string): Promise<void> {
  await this.run("send-keys", "-t", target, "-l", text);
}
```

**Key distinction**:
- `sendKeys(...keys)` — sends tmux **key names** (e.g., "Enter", "Up", "C-u")
- `sendKeysLiteral(text)` — sends **literal text** with `-l` flag (prevents special char interpretation)

**File**: `src/core/transport/tmux-class.ts:440-446` | **Lines**: 440–446

### Mode Safety & Confirm-on-Submit: `src/core/transport/tmux-class.ts:459–537`

The core fix for the send-keys reliability issue (the user's reported buffer-stuck problem):

```typescript
/**
 * Leave copy-mode / transient tmux modes before delivering text.
 * 
 * tmux `send-keys -l` is not mode-safe: in copy-mode literal text is still
 * interpreted by the mode key table, so uppercase/status text can exit the
 * mode mid-string and make tmux print repeated "not in a mode" errors for
 * the remaining characters. `maw hey` wants message delivery, not copy-mode
 * navigation, so high-level text sends normalize the pane first.
 */
async exitModeIfNeeded(target: string): Promise<boolean> {
  let inMode = false;
  try {
    inMode = (await this.run("display-message", "-t", target, "-p", "#{pane_in_mode}")).trim() === "1";
  } catch {
    // If the probe fails, let the subsequent send surface the real target
    // error (for example "can't find pane") instead of hiding it here.
    return false;
  }
  if (!inMode) return false;
  try {
    await this.run("send-keys", "-t", target, "-X", "cancel");
    return true;
  } catch (e: any) {
    // The pane can leave copy-mode between probe and cancel; that race is
    // harmless and should not block delivery.
    if (String(e?.message ?? e).includes("not in a mode")) return false;
    throw e;
  }
}

/**
 * Smart text sending — uses load-buffer for multiline/long messages,
 * send-keys for short single-line. Always submits with Enter.
 *
 * #6 — submit is now confirmed, not fire-and-forget. After placing the
 * text we send Enter, re-inspect the pane, and retry the Enter only while
 * the input line still holds un-submitted content.
 */
async sendText(target: string, text: string): Promise<void> {
  await this.exitModeIfNeeded(target);
  
  if (text.includes("\n") || text.length > 500) {
    // Buffer method — reliable for multiline/long content
    await this.loadBuffer(text);
    await this.pasteBuffer(target);
  } else {
    // Literal send — -l prevents tmux from interpreting special chars like |
    await this.sendKeysLiteral(target, text);
  }
  
  await new Promise(r => setTimeout(r, SEND_SETTLE_MS));
  await this.submitWithConfirm(target, text);
}

/**
 * Send Enter, then confirm the input line cleared before returning. Retries
 * the Enter while input is still pending.
 */
private async submitWithConfirm(target: string, sentText: string): Promise<void> {
  for (let attempt = 1; attempt <= MAX_SUBMIT_ATTEMPTS; attempt++) {
    await this.sendKeys(target, "Enter");
    await new Promise(r => setTimeout(r, SUBMIT_CONFIRM_MS));
    if (!(await this.paneInputPending(target, sentText))) return; // submitted — done
  }
  // Exhausted every retry and the input line still looks non-empty.
  console.warn(
    `[tmux] sendText: ${target} still shows pending input after ${MAX_SUBMIT_ATTEMPTS} Enter attempts — command may not have submitted`,
    // ... more context
  );
}
```

**Constants controlling retry behavior** (from lines 11–23):
```typescript
/** Wait after paste/literal-send before the first Enter — lets the input settle. */
const SEND_SETTLE_MS = 1500;
/** Wait after each Enter before re-checking whether the input line cleared. */
const SUBMIT_CONFIRM_MS = 700;
/** Max Enter attempts before giving up and warning */
const MAX_SUBMIT_ATTEMPTS = 4;
```

**The solution to buffer-stuck**:
1. **Detect copy-mode** via `display-message -p #{pane_in_mode}` before sending text
2. **Exit mode** if needed via `send-keys -X cancel` (safe race-tolerant)
3. **Use buffer for long/multiline text** (avoids single-line size limits)
4. **Confirm Enter was received** by re-capturing pane content and checking for the sent text
5. **Retry Enter up to 4 times** while input is still pending (rather than blind 3x Enter)

**File**: `src/core/transport/tmux-class.ts:459–537` | **Lines**: 459–537

### High-Level Transport Wrapper: `src/transports/tmux.ts`

The TmuxTransport adapter connects the Tmux class to the unified Transport interface:

```typescript
export class TmuxTransport implements Transport {
  readonly name = "tmux";
  private _connected = false;
  private msgHandlers = new Set<(msg: TransportMessage) => void>();
  private presenceHandlers = new Set<(p: TransportPresence) => void>();
  private feedHandlers = new Set<(e: FeedEvent) => void>();

  constructor(
    private readonly sendToTmux: typeof sendKeys = sendKeys,
    private readonly listTmuxSessions: typeof listSessions = listSessions,
    private readonly findTmuxWindow: (sessions: Session[], query: string) => string | null = findWindow,
  ) {}

  get connected() { return this._connected; }

  async connect(): Promise<void> {
    // tmux is always "connected" if we're on the host
    this._connected = true;
  }

  /** Send message via tmux send-keys — only works for local targets */
  async send(target: TransportTarget, message: string): Promise<boolean> {
    if (target.host && target.host !== "local" && target.host !== "localhost") {
      return false; // Not a local target
    }

    try {
      // Resolve tmux target if not provided
      let tmuxTarget = target.tmuxTarget;
      if (!tmuxTarget) {
        const sessions = await this.listTmuxSessions();
        tmuxTarget = this.findTmuxWindow(sessions, target.oracle);
        if (!tmuxTarget) return false;
      }

      await this.sendToTmux(tmuxTarget, message);
      return true;
    } catch {
      return false;
    }
  }

  onMessage(handler: (msg: TransportMessage) => void) {
    this.msgHandlers.add(handler);
  }

  /** tmux transport can reach any local target */
  canReach(target: TransportTarget): boolean {
    return !target.host || target.host === "local" || target.host === "localhost";
  }
}
```

**File**: `src/transports/tmux.ts:14–82` | **Lines**: 14–82

---

## 3. Messaging & Routing Layer

### Route Resolution: `src/core/routing.ts`

The unified `resolveTarget()` function is the single source of truth for all routing (CLI `maw hey`, API `/api/send`, etc.):

```typescript
/**
 * Resolve a query to a local target, remote peer, or null.
 * Sync and read-only — no network calls. Testable without mocks.
 * 
 * Resolution order:
 *   1. Exact tmux pane address (e.g., "47-mawjs:1.0")
 *   2. Fleet config → oracle name → session name → window
 *   3. Session alias convention (e.g., "mawjs" → "mawjs-oracle" window)
 *   4. Local findWindow (bare name fallback)
 *   5. Node:prefix syntax (e.g., "mba:homekeeper")
 *   6. OracleManifest lookup (unified 5-registry registry)
 *   7. Agents map (config.agents)
 *   8. Peer alias (peers.json)
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
    hint: "usage: maw hey <agent> <message>" 
  };

  // Filter out read-only mirrors and federated records
  const writable = sessions.filter(s =>
    !s.name.endsWith("-view") &&
    (s.source === undefined || s.source === "local"),
  );

  const selfNode = config.node ?? "local";

  // --- Step 1: Exact tmux pane address (e.g., "47-mawjs:1.0") ---
  const exactTmuxAddress = resolveExactTmuxPaneAddress(query, writable, "local");
  if (exactTmuxAddress) return exactTmuxAddress;

  // --- Step 2: Fleet config ---
  const fleetSession = resolveFleetSession(query) || resolveFleetSession(query.replace(/-oracle$/, ""));
  if (fleetSession) {
    const fleetResult = resolveFleetWindowTarget(fleetSession, query, writable, "local");
    if (fleetResult) return fleetResult;
  }

  // --- Step 3: Session alias convention (oracle-name → oracle-window) ---
  if (!query.includes(":")) {
    const sessionAliasResult = resolveSessionAliasWindowTarget(query, writable, "local");
    if (sessionAliasResult) return sessionAliasResult;
  }

  // --- Step 4: Local findWindow ---
  const localTarget = findWindow(writable, query, currentSession);
  if (localTarget) {
    return { type: "local", target: localTarget };
  }

  // --- Step 5: Node:prefix syntax (e.g., "mba:homekeeper") ---
  if (query.includes(":") && !query.includes("/")) {
    const colonIdx = query.indexOf(":");
    const nodeName = query.slice(0, colonIdx);
    const agentName = query.slice(colonIdx + 1);
    
    // Self-node check
    if (nodeName === selfNode || nodeName === "local") {
      const selfFleet = resolveFleetSession(agentName) || resolveFleetSession(agentName.replace(/-oracle$/, ""));
      if (selfFleet) {
        const fleetResult = resolveFleetWindowTarget(selfFleet, agentName, writable, "self-node");
        if (fleetResult) return fleetResult;
      }
      const selfTarget = findWindow(writable, agentName, currentSession);
      if (selfTarget) return { type: "self-node", target: selfTarget };
      return { 
        type: "error", 
        reason: "self_not_running", 
        detail: `'${agentName}' not found in local sessions on ${selfNode}`, 
        hint: `maw wake ${agentName}` 
      };
    }

    // Remote node: find peer URL
    const peerUrl = findPeerUrl(nodeName, config);
    if (peerUrl) {
      return { type: "peer", peerUrl, target: agentName, node: nodeName };
    }
    
    return { 
      type: "error", 
      reason: "unknown_node", 
      detail: `node '${nodeName}' not in namedPeers or peers`, 
      hint: "add to maw.config.json namedPeers" 
    };
  }

  // --- Step 6: OracleManifest (unified registry) ---
  const manifestEntry = lookupManifestEntry(query);
  if (manifestEntry?.node && manifestEntry.node !== selfNode && manifestEntry.node !== "local") {
    const peerUrl = findPeerUrl(manifestEntry.node, config);
    if (peerUrl) {
      return { type: "peer", peerUrl, target: query, node: manifestEntry.node };
    }
  }

  // --- Step 7: Agents map ---
  const agentNode = config.agents?.[query] || config.agents?.[query.replace(/-oracle$/, "")];
  if (agentNode) {
    if (agentNode === selfNode) return { 
      type: "error", 
      reason: "self_not_running", 
      detail: `'${query}' mapped to ${selfNode} (local) but not found in sessions`, 
      hint: `maw wake ${query}` 
    };

    const peerUrl = findPeerUrl(agentNode, config);
    if (peerUrl) {
      return { type: "peer", peerUrl, target: query, node: agentNode };
    }
  }

  // --- Step 8: Not resolved ---
  return { 
    type: "error", 
    reason: "not_found", 
    detail: `'${query}' not in local sessions, agents map, or peer aliases`, 
    hint: "check: maw ls" 
  };
}
```

**Key design**:
- **Purely synchronous** — no network I/O (routing is on the hot path)
- **Additive fallback chain** — each step is independent; missing info → continue
- **Error hints** — every failure suggests a corrective command
- **Fleet config first** — convention-driven (e.g., `mawjs-oracle` window for `mawjs` oracle)

**File**: `src/core/routing.ts:62–200` | **Lines**: 62–200

### High-Level Send: `src/core/transport/ssh.ts:209–260`

The transport layer that handles special keys and multi-line text:

```typescript
async function sendKeys(target: string, text: string, host?: string): Promise<void> {
  const t = io.createTmux(host);

  // Special keys → send as tmux key names (no Enter appended)
  const SPECIAL_KEYS: Record<string, string> = {
    "\x1b": "Escape",
    "\x1b[A": "Up",
    "\x1b[B": "Down",
    "\x1b[C": "Right",
    "\x1b[D": "Left",
    "\r": "Enter",
    "\n": "Enter",
    "\b": "BSpace",
    "\x15": "C-u",  // Ctrl+U
  };
  
  if (SPECIAL_KEYS[text]) {
    if (text !== "\x1b") await t.exitModeIfNeeded(target);
    await t.sendKeys(target, SPECIAL_KEYS[text]);
    return;
  }

  // Strip trailing \r or \n — Enter is appended separately
  const endsWithEnter = text.endsWith("\r") || text.endsWith("\n");
  const body = endsWithEnter ? text.slice(0, -1) : text;

  if (!body) {
    await t.exitModeIfNeeded(target);
    await t.sendKeys(target, "Enter");
    return;
  }

  if (body.startsWith("/")) {
    // Slash commands: send char by char for interactive tools (Claude Code, etc.)
    await t.exitModeIfNeeded(target);
    for (const ch of body) {
      await t.sendKeysLiteral(target, ch);
    }
    await t.sendKeys(target, "Enter");
  } else {
    // Smart send — uses buffer for multiline/long, send-keys for short
    await t.sendText(target, body);
  }
}
```

**Behaviors**:
- **Special keys** (Escape, arrow keys, Ctrl+U) → sent as tmux key names  
- **Slash commands** → sent char-by-char (lets Claude Code readline work)
- **Multiline / long text** → use buffer (load-buffer → paste-buffer)
- **Short text** → direct sendKeysLiteral

**File**: `src/core/transport/ssh.ts:209–260` | **Lines**: 209–260

---

## 4. Agent Spawn Path: `maw workon`

### Implementation: `src/vendor/mpr-plugins/workon/impl.ts`

The full flow for spawning a new agent worktree:

```typescript
export async function cmdWorkon(repo: string, task?: string, opts: { layout?: WorktreeLayout } = {}): Promise<void> {
  // Step 1: Resolve repo path (supports "org/repo" or bare "repo")
  const { repoPath, repoName, parentDir } = await resolveRepo(repo);

  let targetPath = repoPath;
  let windowName = repoName;

  if (task) {
    task = sanitizeWorkonTaskSlug(task);
    const worktrees = await findWorktrees(parentDir, repoName);
    const resolved = resolveWorktreeTarget(task, worktrees);
    
    let match: { path: string; name: string } | null = null;
    switch (resolved.kind) {
      case "exact":
      case "fuzzy":
        match = resolved.match;
        break;
      case "ambiguous":
        console.error(`\x1b[31m✗\x1b[0m '${task}' is ambiguous — matches ${resolved.candidates.length} worktrees:`);
        for (const c of resolved.candidates) {
          console.error(`\x1b[90m    • ${c.name}\x1b[0m`);
        }
        throw new Error(`'${task}' is ambiguous — matches ${resolved.candidates.length} worktrees`);
      case "none":
        match = null;
        break;
    }

    // Step 2a: Reuse existing worktree if found
    if (match) {
      console.log(`\x1b[33m⚡\x1b[0m reusing worktree: ${match.path}`);
      targetPath = match.path;
    } else {
      // Step 2b: Create new git worktree
      const nums = worktrees.map(w => parseInt(w.name) || 0);
      const nextNum = nums.length > 0 ? Math.max(...nums) + 1 : 1;
      const wtName = `${nextNum}-${task}`;
      const layout = normalizeWorktreeLayout(opts.layout);
      const wtPath = worktreePathForLayout({ repoPath, parentDir, repoName, wtName, layout });
      const branch = `agents/${wtName}`;

      // Clean up any existing branch
      try { await hostExec(`git -C '${repoPath}' branch -D '${branch}' 2>/dev/null`); } catch { /* expected */ }
      
      // Create worktree directory if nested layout
      if (layout === "nested") await hostExec(`mkdir -p '${repoPath.replace(/'/g, "'\\''")}/agents'`);
      
      // Create git worktree
      await hostExec(`git -C '${repoPath}' worktree add '${wtPath}' -b '${branch}'`);
      console.log(`\x1b[32m+\x1b[0m worktree: ${wtPath} (${branch})`);
      targetPath = wtPath;
    }
    windowName = `${repoName}-${task}`;
  }

  // Step 3: Detect current tmux session
  if (!process.env.TMUX) {
    throw new Error("not in a tmux session — run inside tmux");
  }
  const session = (await hostExec("tmux display-message -p '#{session_name}'").catch(() => "")).trim();
  if (!session) {
    throw new Error("could not detect current tmux session");
  }

  // Step 4: Check for existing window (prevent duplicate)
  const existingWindows = await tmux.listWindows(session).catch(() => [] as { name: string }[]);
  const existing = existingWindows.find(w => w.name === windowName);
  if (existing) {
    await tmux.selectWindow(`${session}:${windowName}`);
    console.log(`\x1b[33m⚡\x1b[0m reusing existing window '${windowName}' in ${session}`);
    return;
  }

  // Step 5: Create tmux window + send startup command
  await tmux.newWindow(session, windowName, { cwd: targetPath });
  await new Promise(r => setTimeout(r, 300));
  await tmux.sendText(`${session}:${windowName}`, buildCommandInDir(windowName, targetPath));

  // Step 6: Register in fleet if this is an oracle
  if (!task && repoName.endsWith("-oracle")) {
    const fleet = ensureFleetSessionEntry({ session, window: windowName, cwd: targetPath, createdBy: "maw workon" });
    if (fleet.status === "created") {
      console.log(`\x1b[32m+\x1b[0m fleet registered ${session}:${windowName}`);
    }
  }

  console.log(`\x1b[32m✅\x1b[0m workon '${windowName}' in ${session} → ${targetPath}`);
}
```

**Sequence**:
1. **Resolve repo** → ghqFind (searches ~/.ghq and config.pluginSources)
2. **Resolve worktree** → search existing worktrees, fuzzy match, or create new
3. **Create git worktree** → `git worktree add` on a new `agents/*` branch
4. **Create tmux window** → `tmux new-window` in detected session
5. **Send startup command** → uses smartText (buffer for multiline, literal for short)
6. **Register in fleet** → adds to `~/.maw/fleet/` if oracle
7. **Select window** → makes it active in tmux

**File**: `src/vendor/mpr-plugins/workon/impl.ts:26–104` | **Lines**: 26–104

---

## 5. Error Handling Idioms

### UserError Class: `src/core/util/user-error.ts`

The error taxonomy separates user-facing failures from unexpected runtime errors:

```typescript
/**
 * UserError signals a user-facing failure — bad input, missing target,
 * unknown command. The top-level error handler catches these and exits 1
 * WITHOUT letting bun print its default stack trace. For genuinely unexpected
 * runtime failures, throw a regular Error so the stack stays visible for
 * debugging.
 *
 * Convention: throw sites may print richer context (colors, hints,
 * suggestions) before throwing. The top-level catch still prints this
 * message so direct UserError throws never disappear silently.
 *
 * Throw UserError for: missing/invalid args, unknown commands, bad
 *   target resolution, help-path exits.
 * Throw regular Error for: genuinely unexpected runtime failures
 *   where the stack is valuable for debugging.
 */
export class UserError extends Error {
  readonly isUserError = true;
  constructor(message: string) {
    super(message);
    this.name = "UserError";
  }
}

export function isUserError(e: unknown): e is UserError {
  return e instanceof Error && (e as { isUserError?: boolean }).isUserError === true;
}
```

**Why a brand field** (not `instanceof`):
- Class identity breaks across module boundaries in ESM (dynamic imports, separate realms)
- Brand survives across realm boundaries

**File**: `src/core/util/user-error.ts` | **Lines**: 1–32

### Top-Level Error Handler: `src/cli/error-handler.ts`

Catches and renders errors with appropriate detail:

```typescript
/**
 * Top-level error handler for `main()`. Always exits — never returns.
 *
 * - UserError: print its message without a bun stack trace, then exit 1.
 *   Some call sites throw UserError directly; keeping it silent hides the
 *   actionable reason (for example wake concurrency refusals).
 * - AmbiguousMatchError: escapes from findWindow via resolver chains
 *   (cmdSend, cmdPeek, talk-to, view, etc.). Render as actionable CLI
 *   output instead of a minified stack trace.
 * - Anything else: print the error normally and exit 1.
 */
export function handleTopLevelError(e: unknown, args: string[]): never {
  if (isUserError(e)) {
    if (e.message) process.stderr.write(`${e.message}\n`);
    process.exit(1);
  }
  if (e instanceof AmbiguousMatchError) {
    console.error(renderAmbiguousMatch(e, args));
    process.exit(1);
  }
  console.error(e);
  process.exit(1);
}
```

**Error rendering strategy**:
- **UserError** → message only (no stack)
- **AmbiguousMatchError** → formatted suggestions (e.g., "did you mean: mawjs or mawjs-oracle?")
- **Other** → full error with stack

**File**: `src/cli/error-handler.ts` | **Lines**: 1–28

### HostExecError: Transport Wrapper

Carries context for where an error originated (target + transport mode):

```typescript
export class HostExecError extends Error {
  readonly target: string;
  readonly transport: HostExecTransport; // "local" | "ssh"
  readonly underlying: Error;
  readonly exitCode?: number;

  constructor(target: string, transport: HostExecTransport, underlying: Error, exitCode?: number) {
    super(`[${transport}:${target}] ${underlying.message}`);
    this.name = "HostExecError";
    this.target = target;
    this.transport = transport;
    this.underlying = underlying;
    this.exitCode = exitCode;
  }
}
```

**Allows callers to**:
- Distinguish SSH timeouts from tmux unavailability
- Log which host/target failed for distributed debugging

**File**: `src/core/transport/ssh.ts:8–22` | **Lines**: 8–22

---

## 6. Testing Approach

### Unit Testing: Bun + Pure Functions

The project uses **Bun's native test runner** with pure-function testing patterns:

```typescript
// test/agents.test.ts — pure function (no tmux, no I/O)
import { describe, test, expect } from "bun:test";
import { buildAgentRows, type AgentRow } from "../src/commands/shared/agents";

function makeWindowNames(entries: Array<[string, string]>): Map<string, string> {
  return new Map(entries);
}

describe("buildAgentRows — oracle detection", () => {
  test("oracle window is included and oracle name is extracted", () => {
    const panes = [{ command: "claude", target: "01-mawjs:mawjs-oracle.0", pid: 1234 }];
    const wn = makeWindowNames([["01-mawjs:0", "mawjs-oracle"]]);
    const rows = buildAgentRows(panes, wn, "oracle-world");
    
    expect(rows).toHaveLength(1);
    expect(rows[0].oracle).toBe("mawjs");
    expect(rows[0].window).toBe("mawjs-oracle");
    expect(rows[0].session).toBe("01-mawjs");
    expect(rows[0].node).toBe("oracle-world");
    expect(rows[0].pid).toBe(1234);
  });

  test("legacy numeric pane target still resolves window name from listAll", () => {
    const panes = [{ command: "claude", target: "01-mawjs:0.0", pid: 1234 }];
    const wn = makeWindowNames([["01-mawjs:0", "mawjs-oracle"]]);
    const rows = buildAgentRows(panes, wn, "oracle-world");
    
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      session: "01-mawjs",
      window: "mawjs-oracle",
      oracle: "mawjs",
    });
  });

  test("non-oracle window is excluded by default", () => {
    const panes = [{ command: "zsh", target: "01-mawjs:shell.0", pid: 5678 }];
    const wn = makeWindowNames([["01-mawjs:1", "shell"]]);
    const rows = buildAgentRows(panes, wn, "oracle-world");
    
    expect(rows).toHaveLength(0);
  });

  test("non-oracle window is included with --all", () => {
    const panes = [{ command: "zsh", target: "01-mawjs:shell.0", pid: 5678 }];
    const wn = makeWindowNames([["01-mawjs:1", "shell"]]);
    const rows = buildAgentRows(panes, wn, "oracle-world", { all: true });
    
    expect(rows).toHaveLength(1);
    expect(rows[0].oracle).toBe("");
    expect(rows[0].window).toBe("shell");
  });
});
```

**File**: `test/agents.test.ts:1–50` | **Lines**: 1–50

### Fake Tmux for Testing send-keys: Injection Pattern

Mock the Tmux class by extending it and overriding `run()`:

```typescript
// test/tmux-class-command-builders.test.ts
import { describe, expect, test } from "bun:test";
import { Tmux } from "../src/core/transport/tmux-class";

type RunCall = { subcommand: string; args: (string | number)[] };
type RunHandler = (subcommand: string, args: (string | number)[], callIndex: number) => string | Promise<string>;

class FakeTmux extends Tmux {
  calls: RunCall[] = [];
  handler: RunHandler;

  constructor(handler: RunHandler = () => "") {
    super(undefined, "");
    this.handler = handler;
  }

  async run(subcommand: string, ...args: (string | number)[]): Promise<string> {
    const callIndex = this.calls.length;
    this.calls.push({ subcommand, args });
    return this.handler(subcommand, args, callIndex);
  }

  callStrings(): string[] {
    return this.calls.map(c => [c.subcommand, ...c.args].join(" "));
  }
}

class FakeSubmitTmux extends Tmux {
  calls: string[] = [];
  captureScript: string[] = [];
  private captureIndex = 0;

  constructor() {
    super(undefined, "");
  }

  async exitModeIfNeeded(target: string): Promise<boolean> {
    this.calls.push(`exitModeIfNeeded:${target}`);
    return true;
  }

  async sendKeysLiteral(_target: string, text: string): Promise<void> {
    this.calls.push(`sendKeysLiteral:${text}`);
  }

  async sendKeys(_target: string, ...keys: string[]): Promise<void> {
    this.calls.push(`sendKeys:${keys.join(",")}`);
  }

  async capture(_target: string, lines = 80): Promise<string> {
    this.calls.push(`capture:${lines}`);
    const next = this.captureScript[this.captureIndex] ?? this.captureScript.at(-1) ?? "";
    this.captureIndex++;
    return next;
  }
}

describe("Tmux command wrapper coverage", () => {
  test("listSessions loads windows per session and fails soft when tmux is absent", async () => {
    const t = new FakeTmux((subcommand, args) => {
      const key = [subcommand, ...args].join(" ");
      return {
        "list-sessions -F #{session_name}": "alpha\nbeta\n",
        "list-windows -t alpha -F #{window_index}:#{window_name}:#{window_active}": "0:main:1\n1:work:0",
        "list-windows -t beta -F #{window_index}:#{window_name}:#{window_active}": "2:solo:1",
      }[key] ?? "";
    });

    expect(await t.listSessions()).toEqual([
      { name: "alpha", windows: [
        { index: 0, name: "main", active: true },
        { index: 1, name: "work", active: false }
      ]},
      { name: "beta", windows: [{ index: 2, name: "solo", active: true }] },
    ]);
  });
});
```

**File**: `test/tmux-class-command-builders.test.ts:1–100` | **Lines**: 1–100

### Coverage Strategy

From the 2026-06-07 documentation:
- **695 TypeScript files** analyzed
- **100% test coverage** (33165/33169 lines)
- **Bun test runner** with per-file subprocess isolation
- **Async/await patterns** (no callbacks, stack traces are readable)
- **Modular mocks** (override single methods, test in isolation)

---

## Integration Summary

### How These Pieces Connect

1. **User types**: `maw workon pops-pet fix/thing`
2. **CLI entry** (`src/cli.ts`) → loads plugins → dispatches to workon plugin
3. **workon plugin** (`src/vendor/mpr-plugins/workon/impl.ts`) → creates git worktree + tmux window
4. **sends startup command** → tmux.sendText() → tmux-class.ts (with retry logic)
5. **User then types**: `maw hey leica "start work"`
6. **Routing** (`src/core/routing.ts`) → finds leica-oracle session/window
7. **Transport** (tmux.ts → tmux-class.ts) → sendKeys with exitModeIfNeeded + confirm-on-submit
8. **Errors** → UserError or AmbiguousMatchError → top-level handler renders to stderr + exits

### Key Design Principles

1. **Sync routing hot-path** — no network I/O on every send
2. **Mode-safe sends** — always check pane state before text delivery
3. **Confirm-on-submit** — re-inspect pane after Enter, retry if input pending
4. **Pure functions** — routing, command building, oracle detection all testable without mocks
5. **Explicit error hierarchy** — UserError (user's mistake), HostExecError (transport), runtime Error (bug)
6. **Fleet-first conventions** — `mawjs` → `mawjs-oracle` window, fallback to bare findWindow

---

## References

- **src/cli.ts** (65 lines) — entry point and bootstrap
- **src/cli/dispatch.ts** (200+ lines) — command dispatch ladder
- **src/core/routing.ts** (330+ lines) — unified route resolver
- **src/core/transport/tmux.ts** (83 lines) — TmuxTransport adapter
- **src/core/transport/tmux-class.ts** (600+ lines) — Tmux class + send-keys reliability
- **src/core/transport/ssh.ts** (300+ lines) — high-level transport wrapper
- **src/core/util/user-error.ts** (32 lines) — error type system
- **src/cli/error-handler.ts** (28 lines) — top-level error rendering
- **src/vendor/mpr-plugins/workon/impl.ts** (105 lines) — agent spawn flow
- **test/agents.test.ts** (84 lines) — pure-function unit tests
- **test/tmux-class-command-builders.test.ts** (100+ lines) — tmux mock tests

**Repository**: https://github.com/Soul-Brews-Studio/maw-js  
**Version**: v26.6.14-alpha.2110  
**License**: BUSL-1.1  
**Build**: Bun + TypeScript  

---

**Generated**: 2026-07-26 21:20 UTC  
**Analysis basis**: maw-js/origin/ repository (v26.6.14-alpha.2110)
