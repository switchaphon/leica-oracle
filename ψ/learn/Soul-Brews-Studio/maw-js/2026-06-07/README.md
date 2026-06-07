# maw-js Learning Materials — 2026-06-07

## Documents

- **1537_ARCHITECTURE.md** (976 lines)
  - Comprehensive architecture deep dive of the maw-js codebase
  - Covers: directory structure, entry points, core abstractions, plugin system, federation protocol, team coordination, channels, configuration, dependencies, API server, testing strategy, security model, performance notes, and future work
  - Audience: Developers building on maw-js or integrating it with the Oracle family

## Quick Facts

- **Codebase**: 695 TypeScript files analyzed
- **Version**: v26.6.8-alpha.1320
- **Build system**: Bun + TypeScript
- **License**: BUSL-1.1
- **Repository**: Soul-Brews-Studio/maw-js

## Key Findings

### Architecture Layers

1. **CLI Layer** (`src/cli.ts`) — Command dispatch ladder (comm → tools → aliases → plugins)
2. **Core Layer** (`src/core/`) — Runtime abstractions (agent status, message queue, routing, fleet management)
3. **Plugin System** (`src/plugin/`) — Dynamic loading, WASM bridge, lifecycle hooks, manifest validation
4. **API Layer** (`src/api/`) — HTTP server (Hono/Elysia), WebSocket streaming, federation endpoints
5. **Transport Layer** (`src/core/transport/`) — Abstract send-keys interface (tmux, SSH, PTY, MQTT, Zenoh)

### Federation Protocol

- **HMAC-SHA256 signing** with v1/v2/v3 versions
- **TOFU public key caching** for per-peer authentication
- **Peer discovery** via static config (peers.json) + mDNS (future)
- **Fleet snapshots** synced across peers for agent awareness

### Core Abstractions

- **Agent Status Machine** (idle → busy → ready) for managing Oracle lifecycle
- **Message Queue + Dispatch Engine** — auto-delivers when agents idle
- **Request-Reply Pattern** — async RPC between peers
- **Unified Routing** (`resolveTarget()`) — same code path for local/peer/manifest targets
- **Fleet Management** — declarative session/window topology

### Plugin System

- **Two types**: TypeScript (full access) and WASM (sandboxed)
- **Manifest validation** with SDK semver gating and artifact hash verification
- **Hooks**: wake, sleep, serve (persistent process), cron, events (gate, filter, on, late)
- **Module surface** — explicit cross-plugin exports via manifest whitelist

## How maw-js Fits the Oracle Family

maw-js is the **orchestration and transport layer** that:

1. Spawns Oracles (Claude Code agents like Leica, Chrome, Neon, Codec, Flux, Static, Wire, Pixel)
2. Routes messages between them (`maw hey <oracle> "<message>"`)
3. Manages their tmux sessions and panes
4. Provides federation for cross-node coordination
5. Exposes HTTP APIs for web dashboards and integrations

It is **not** an AI itself — it is the **nervous system** connecting AI agents into a coordinated team.

## Integration Points for Leica Oracle

As the Father Oracle (Leica), you will interact with maw-js through:

1. **CLI commands**: `maw workon`, `maw hey`, `maw team up`, `maw spawn`, `maw gather`, `maw scatter`
2. **HTTP API** (`localhost:7777`): `/api/send`, `/api/wake`, `/api/federation/status`
3. **Message routing**: Messages queued in `MessageQueue` and auto-delivered via `DispatchEngine`
4. **Fleet config** (`~/.maw/fleet/`): Declares all Oracles, sessions, and peer nodes
5. **Plugin system**: Custom commands and handlers extend maw-js functionality
6. **Channel system**: Discord integration (future), MQTT, Zenoh transports

## Next Steps

- Review the full architecture document for deep technical details
- Examine test files (`test/`) for real usage patterns and edge cases
- Profile with Leica's memory system — store key patterns in `ψ/learn/` for future reference
- Use `/trace` skill to cross-reference implementations with learnings

---

**Generated**: 2026-06-07 15:37 UTC  
**Analysis by**: Leica Oracle System Agent  
**Confidence**: High (comprehensive codebase analysis, 695 TS files)
