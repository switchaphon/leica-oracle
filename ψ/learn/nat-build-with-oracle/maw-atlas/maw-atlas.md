# maw-atlas Learning Index

## Source
- **Origin**: ./origin/
- **GitHub**: https://github.com/nat-build-with-oracle/maw-atlas

## Explorations

### 2026-06-07 1405 (deep)
- [[2026-06-07/1405_ARCHITECTURE|Architecture]]
- [[2026-06-07/1405_CODE-SNIPPETS|Code Snippets]]
- [[2026-06-07/1405_QUICK-REFERENCE|Quick Reference]]
- [[2026-06-07/1405_TESTING|Testing]]
- [[2026-06-07/1405_API-SURFACE|API Surface]]

**Key insights**:
- Discord fleet infrastructure plugin for maw-js — manage bots, channels, guilds, threads from CLI
- watch → route → spawn-session orchestration chain for auto-spawning workers from Discord threads
- Guard gates (allowFrom, maxWorktrees) enforce security before spawn
- Reverse bridge: Codex pane output → Discord with diff detection
- Atomic file I/O (tmp + rename), snowflake ID comparison for message ordering
