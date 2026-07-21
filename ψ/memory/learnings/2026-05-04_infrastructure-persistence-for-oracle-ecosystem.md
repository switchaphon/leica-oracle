---
title: Infrastructure Persistence for Oracle ecosystem: (1) macOS LaunchAgents with Run
tags: [launchagent, daemon, arra-oracle, playwright, infrastructure, persistence]
created: 2026-05-04
source: rrr --deep: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Infrastructure Persistence for Oracle ecosystem: (1) macOS LaunchAgents with Run

Infrastructure Persistence for Oracle ecosystem: (1) macOS LaunchAgents with RunAtLoad+KeepAlive for 3 daemons — maw serve (:3456), maw-ui (:5173), arra-oracle HTTP (:47778). PATH must include ~/.bun/bin. Logs to ~/.maw/logs/. (2) arra-oracle-v3 has a full Elysia HTTP server at port 47778 with 15 route modules, Swagger, Drizzle ORM — connects to studio.buildwithoracle.com. Start: `cd arra-oracle-v3 && bun src/server.ts`. (3) Playwright CLI beats MCP for browser automation — batch scripts, clear timeouts, no 33-minute hangs. Applied as project-wide directive to pops-clinic via inbox + CLAUDE.md + settings.

---
*Added via Oracle Learn*
