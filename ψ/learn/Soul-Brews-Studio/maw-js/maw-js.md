# maw-js Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/maw-js

## Explorations

### 2026-06-07 1537 (deep)
- [[2026-06-07/1537_ARCHITECTURE|Architecture]]
- [[2026-06-07/1537_CODE-SNIPPETS|Code Snippets]]
- [[2026-06-07/1537_QUICK-REFERENCE|Quick Reference]]
- [[2026-06-07/1537_TESTING|Testing]]
- [[2026-06-07/1537_API-SURFACE|API Surface]]

**Key insights**:
- Multi-Agent Workflow orchestrator — tmux session management, fleet coordination, federation protocol
- maw is NOT an AI — it's the orchestration layer that manages Claude Code agents (Oracles)
- Federation: trustless HMAC v1/v2/v3 signing, TOFU pubkeys, no central coordinator
- 89+ plugins, 80+ CLI commands, 695 TypeScript files
- 100% test coverage (33165/33169 lines), Bun test runner with per-file subprocess isolation
- Plugin SDK: InvokeContext/InvokeResult with capabilities gating
- Team coordination: charter YAML → team up → spawn → gather → scatter
- Transport abstraction: tmux/SSH/MQTT/Zenoh swappable without app logic changes
