---
source: "rrr --deep: leica-oracle"
date: 2026-05-04
tags: [launchagent, daemon, infrastructure, arra-oracle, persistence]
confidence: high
---

# Infrastructure Persistence — LaunchAgents + arra-oracle HTTP Server

## Pattern 1: macOS LaunchAgents for Oracle Daemons

Three always-on services via `~/Library/LaunchAgents/`:

| Service | Plist | Port | Command |
|---------|-------|------|---------|
| maw serve | `com.soulbrews.maw-serve.plist` | 3456 | `maw serve` |
| maw-ui | `com.soulbrews.maw-ui.plist` | 5173 | `bun run dev` (in maw-ui dir) |
| arra-oracle | `com.soulbrews.arra-oracle.plist` | 47778 | `bun src/server.ts` (in arra-oracle-v3 dir) |

Key config: `RunAtLoad: true` + `KeepAlive: true`. PATH must include `~/.bun/bin`. Logs to `~/.maw/logs/`.

## Pattern 2: arra-oracle HTTP Server

- Full Elysia server at port 47778 with 15 route modules, Swagger, Drizzle ORM
- Lives in repo: `~/ghq/.../Soul-Brews-Studio/arra-oracle-v3/src/server.ts`
- CORS allows `studio.buildwithoracle.com` and all localhost origins
- PID file at `oracle-http.pid` for process management
- Start: `cd arra-oracle-v3 && bun src/server.ts`

## Pattern 3: Playwright CLI over MCP

Switched pops-clinic from Playwright MCP (8 permissions, round-trip per action, 33-min hang) to CLI (batch scripts, clear timeouts). Applied as project-wide directive via inbox + CLAUDE.md + settings.local.json.

## Connection

These three patterns together make the Oracle ecosystem persistent and self-sufficient — services survive reboots, browser testing is reliable, and the HTTP API connects to the cloud studio.
