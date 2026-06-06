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
