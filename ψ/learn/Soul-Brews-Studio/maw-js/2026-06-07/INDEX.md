# MAW-JS Learning Index

**Learning Session**: 2026-06-07  
**Source Repo**: Soul-Brews-Studio/maw-js (v26.6.8-alpha.1320)  
**Focus Areas**: Multi-Agent Workflow CLI, Federation Protocol, Plugin Architecture

---

## Files in This Learning Session

### 1537_CODE-SNIPPETS.md
Comprehensive code samples from maw-js covering:

**Core Architecture**
- CLI entry point & command dispatch hierarchy
- Session management API (wake, sleep, send)
- Team coordination (liveness, broadcasting)
- Fleet management & configuration

**Federation**
- Peer discovery & reachability checks
- HMAC-SHA256 authentication (v1/v2/v3)
- Target resolution routing (local → peer → manifest)
- Protected routes & auth middleware

**Plugin System**
- Plugin registry & discovery flow
- Semver gating & artifact verification
- SDK surface (InvokeContext, InvokeResult)
- HTTP plugin API (GET/POST routes)

**Transport**
- Tmux abstraction layer (types, class, locking)
- SSH session management
- HTTP proxy for LAN peers

**Key Patterns**
- Dependency injection (Deps interfaces)
- Error handling (UserError vs transport)
- Lazy caching (plugin discovery)
- Validation gates (semver, HMAC window)

---

## Quick Navigation

| Topic | Lines | Purpose |
|-------|-------|---------|
| CLI Entry (src/cli.ts) | 1-80 | Bootstrap, argument parsing, plugin loading |
| Dispatch (src/cli/dispatch.ts) | 80-150 | Command routing ladder, plugin resolution |
| Sessions API (src/api/sessions.ts) | 180-250 | Wake/sleep/send routes, DI pattern |
| Sleep Flow (src/lib/sleep.ts) | 250-380 | Graceful shutdown, window detection |
| Teams (src/api/teams.ts + src/engine/teams.ts) | 380-550 | Liveness checking, pane validation |
| Fleet (src/api/fleet.ts) | 550-650 | Fleet config discovery & aggregation |
| Federation (src/api/federation.ts) | 650-750 | Status API, peer discovery surface |
| Peers (src/core/transport/peers.ts) | 750-850 | Reachability probing, aggregation, cache |
| HMAC Auth (src/lib/federation-auth.ts) | 850-950 | v1/v2/v3 signing, body hashing |
| Elysia Auth (src/lib/elysia-auth.ts) | 950-1050 | HMAC middleware, request capture |
| Plugin Registry (src/plugin/registry.ts) | 1050-1150 | Discovery, semver, dev-mode detection |
| Plugin SDK (packages/sdk/plugin.ts) | 1150-1200 | Public authoring surface |
| Plugins API (src/api/plugins.ts) | 1200-1320 | GET/POST routes, invoke flow |
| Routing (src/core/routing.ts) | 1320-1450 | Target resolution order, manifest lookup |
| Tmux Transport (src/core/transport/tmux.ts) | 1450+ | Abstraction barrel, submodule exports |

---

## Key Discoveries

### 1. Command Dispatch is Multi-Layered
Routes flow through:
1. `routeComm` (list/peek/send shortcuts)
2. `routeTools` (built-in commands)
3. Top-level aliases
4. Plugin command registry (prefix-match with ambiguity detection)
5. Bundled plugin registry fallback

Allows rich plugin ecosystem without collisions.

### 2. Federation Auth is Additive
- **v1** (legacy): unsigned, allows body replay
- **v2** (current): SHA256(body) bound to signature, mitigates body swap
- **v3** (emerging): adds per-peer ed25519 signing on top of v2

No breaking changes — v1 peers still work.

### 3. Plugin Discovery Caches Per-Process
`_discoverCache` is cleared only on:
- Plugin install/uninstall
- Test suite (explicit reset)
- Config reload

Saves ~50ms per discovery call (measured in profiler).

### 4. Session Filtering Excludes Mirrors
`-view` suffix sessions are federated mirrors from other peers. Local `maw send` only routes to writable (`source: undefined || "local"`) sessions.

### 5. Team Liveness is Heuristic
Checks:
- **tmux-mode**: pane still exists
- **in-process**: cwd is local + joined < 2h ago
- **team-lead**: cwd locality + recency (not just pane)

Handles stale session records from remote machines.

### 6. Manifest Lookup is Sync with 30s TTL
`resolveTarget()` is fully synchronous (no async network calls). Manifest caching makes hot-path cost a single in-memory Map lookup.

Manifest resolution order:
1. Local findWindow (exact match)
2. Fleet config (oracle-name → session)
3. Manifest entry (agents array, cached 30s)
4. Agents map (legacy, deprecated)
5. Peer alias (peers.json)

### 7. HMAC Window is ±5 Minutes
Both v1/v2/v3 use `WINDOW_SEC = 300`. Clock drift > 3min triggers warning (early alert before 5min hard fail).

Enables fleet-wide clock skew detection without time-sync tools.

---

## Architecture Highlights

### Dependency Injection Everywhere
All API modules expose a `create*Api(deps)` factory + `const api = create*Api()` default export. Makes testing easy without mocks.

### Soft Federation Boundaries
Peers communicate via HTTP with:
- Read-only endpoints public (GET /api/sessions)
- Write endpoints protected (POST /api/send, /api/wake)
- Plugin invocation guarded by HMAC

No gossip protocol, no consensus — just HTTP.

### Plugin Lifecycle Hooks
Plugins can hook wake/sleep/send lifecycle via:
```typescript
runWakeLifecycleHooks({ oracle, session, window })
runSleepLifecycleHooks({ oracle, session, window })
```

Lets plugins (e.g., discord bridge) react to agent events.

### Error Handling Tiers
1. **CLI User**: `UserError` → caught at top level, human message
2. **Transport**: HTTP status codes (401, 404, 405, 500)
3. **Plugin**: flag validation before invoke, exit code on fail

---

## Files to Deep-Dive Next

- `src/commands/shared/wake-resolve.ts` — fetch issue prompts, resolve fleet sessions
- `src/lib/oracle-manifest.ts` — manifest loading, caching, lineage computation
- `src/lib/peers/store.ts` — TOFU pubkey pinning, peer identity
- `src/core/runtime/find-window.ts` — session/window/pane matching logic
- `src/plugin/lifecycle.ts` — wake/sleep/send hook orchestration

---

**Scanned**: ~80 files from maw-js source  
**Snippets Extracted**: 10 key modules  
**LOC Covered**: ~1,500+ lines of production code  
**Date**: 2026-06-07 15:37 UTC
