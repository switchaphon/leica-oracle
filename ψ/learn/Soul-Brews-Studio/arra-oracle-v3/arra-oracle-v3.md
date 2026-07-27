# arra-oracle-v3 Learning Index

## Source
- **Origin**: ./origin/ (points at the `main` clone — the pre-upgrade rollback point, `77e17529`)
- **Alpha clone (now live)**: `~/ghq/github.com/Soul-Brews-Studio/arra-oracle-v3-alpha`
- **GitHub**: https://github.com/Soul-Brews-Studio/arra-oracle-v3

## Explorations

### 2026-07-26 2135 (default+delta) — upgrade assessment, then upgraded
- [[2026-07-26/2135_ARCHITECTURE|Architecture]]
- [[2026-07-26/2135_QUICK-REFERENCE|Quick Reference — full MCP tool tables]]
- [[2026-07-26/2135_UPGRADE-DELTA|Upgrade Delta — risk analysis]]

**Key insights**:
- Same branch pattern as maw: **`alpha` is the active line, `main` is stale.** We were running
  `main` @ `77e17529` (26.6.1-alpha.1506, 14 June) — **1,176 commits behind** alpha.
- **Tool surface is purely additive**: all 21 tools we used survive, 8 new ones added, zero
  removed. Verified by booting the alpha server and reading `tools/list` — **30 tools exposed**.
- **Migrations auto-apply, ungated.** `src/storage/drizzle-sqlite.ts:69` calls
  `migrate(db, {migrationsFolder})` inside `initializeDrizzleSqlite()` with no flag or prompt —
  the DB migrates the instant the storage layer opens it. A backup is mandatory, and rollback
  needs the DB restored, not just the config repointed.
- **Dry-run proof** (migrated a *copy*, not the live DB): 15 → 42 migrations, 22 → 35 tables,
  and every row survived — `oracle_documents` 179→179, `forum_threads` 14→14,
  `forum_messages` 61→61. `oracle_search` returned real results post-migration.
- **Two separate databases exist.** The stdio MCP server uses `~/.oracle/oracle.db` (1.1M);
  a long-running HTTP server (PID 1144, since 10 July, port 47778) uses
  `~/.arra-oracle-v2/oracle.db` (2.1M). They do **not** share state, so migrating the MCP DB
  cannot corrupt the HTTP server's.
- **The one real breaking change** (per delta analysis): the raw HTTP federation/peer subsystem
  — TOFU pinning, peer registry, `/api` peer routes — was **deleted wholesale** in alpha and
  replaced by MCP-native bridge tools. Harmless for us: our federation goes through maw, and
  nothing in our config calls arra's peer HTTP routes.
- Bug fix we inherit: in `main`, an `ORACLE_ENABLED_TOOLS` allow-list naming only unrecognised
  tools silently disabled the **entire** MCP surface. Alpha guards against it
  (`tool-groups-core.ts:153-157`).
- Caveat on the repo: alpha commits a Rust/Cargo build-artifact tree under
  `frontend/src-tauri/target/` — ~2,969 of 5,317 changed files are dead weight in every clone.
  Doesn't affect runtime.

**Action taken 2026-07-26**: cloned alpha to a dedicated dir, `bun install`, dry-run migration
against a copy, then repointed `~/.claude.json` → alpha. Backups:
`~/.oracle.bak-2026-07-26`, `~/.arra-oracle-v2.bak-2026-07-26`, `~/.claude.json.bak-2026-07-26`.
Takes effect on next Claude Code restart.
