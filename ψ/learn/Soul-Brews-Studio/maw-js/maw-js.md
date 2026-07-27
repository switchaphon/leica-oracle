# maw-js Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/Soul-Brews-Studio/maw-js

## Explorations

### 2026-07-26 2120 (default) — migration assessment vs maw-rs
- [[2026-07-26/2120_ARCHITECTURE|Architecture]]
- [[2026-07-26/2120_CODE-SNIPPETS|Code Snippets]]
- [[2026-07-26/2120_QUICK-REFERENCE|Quick Reference]]

**Key insights**:
- **maw-js has declared its own ceiling.** `docs/maw-rs-port-status.md`: "maw-js has
  reached the practical coverage ceiling… Remaining work belongs in maw-rs crate/CLI
  parity issues rather than maw-js coverage work" and "maw-js remains the coordination
  layer and source of truth **until maw-rs reaches CLI parity**."
- Development has effectively stopped: last release **v26.6.14-alpha.2110 (2026-06-13)**,
  only **2 commits in the last 30 days**, and 7 of the 8 most recent PRs sit **OPEN**
  (Windows fixes stalled since 18–22 July).
- Role has shifted from product to **spec/fixture source of truth** — it owns the
  portable `test/spec/*.fixtures.json` that maw-rs implements against.
- Our install is pinned to commit `3318389` (2026-06-06, v26.6.6-alpha.1652), **459
  commits behind** alpha HEAD. That gap is mostly maintenance: 72 dependency bumps,
  34 fixes, 19 tests — only **8 feature commits**.
- Runtime: Bun-only, executes `src/cli.ts` directly. 108 plugins load as Bun/TS
  symlinks from `~/.maw/plugins/`.

See the cross-repo decision doc: [[../../../memory/learnings/2026-07-26_maw-js-vs-maw-rs-migration|maw-js vs maw-rs migration assessment]]

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
