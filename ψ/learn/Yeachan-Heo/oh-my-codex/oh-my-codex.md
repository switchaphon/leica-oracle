# oh-my-codex Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Yeachan-Heo/oh-my-codex

## Explorations

### 2026-05-24 1655 (manual — Haiku agents exceeded context)
- [[2026-05-24/1655_OVERVIEW|Full Overview]]

**Key insights**:
- OMX is a workflow layer for OpenAI Codex CLI (not Claude) — adds structured planning, multi-agent teams, and durable state
- Architecture: TypeScript CLI + 6 Rust crates for performance-critical paths
- Canonical workflow: $deep-interview → $ralplan → $ultragoal
- Comparable in spirit to our Oracle system but for a different AI and with different philosophy

### 2026-06-06 1808 (default)
- [[2026-06-06/1808_ARCHITECTURE|Architecture]]
- [[2026-06-06/1808_CODE-SNIPPETS|Code Snippets]]
- [[2026-06-06/1808_QUICK-REFERENCE|Quick Reference]]

**Key insights**:
- Rust core: event-sourced state machine with file-based locking and crash recovery via authority leases
- Team coordination: tmux workers, file-based task queues with claim/release, git worktree isolation
- Auth hotswap + token rotation for quota management — relevant pattern for our fleet
- v0.18.9: 30+ agent roles, autopilot FSM, coordination protocol

### 2026-06-19 1339 (deep)
- [[2026-06-19/1339_ARCHITECTURE|Architecture — Rust runtime, authority leasing, autopilot FSM]]
- [[2026-06-19/1339_CODE-SNIPPETS|Code Snippets — spawn, resume, state, HUD, plugin]]
- [[2026-06-19/1339_QUICK-REFERENCE|Quick Reference — all CLI commands, config, env vars]]
- [[2026-06-19/1339_TESTING|Testing — 357 tests, team runtime, quality gates]]
- [[2026-06-19/1339_API-SURFACE|API Surface — hooks, MCP, sidecar, AGENTS.md]]

**Key insights**:
- v0.18.13: production-grade, 357 test files, Rust+TS hybrid
- omx was NEVER INSTALLED on leica node — "engine:omx bugs" were missing-binary symptoms, not software defects
- Nat's 3 teams (ting/tee/arra) ran omx at scale: 115 PRs, 7 coders — it works when properly set up
- Installation is trivial: `bun install -g oh-my-codex && omx setup && omx doctor`
- maw needs engine registry config to map `engine: omx` → omx binary
- Retirement correction needed: we taught 9 oracles to avoid a tool that was never installed
