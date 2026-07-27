# arra-oracle-v3: Upgrade Delta — `main` (running) → `alpha` (latest)

**Prepared**: 2026-07-26 21:35 · **For**: go/no-go decision on upgrading the live arra-oracle-v3 MCP server

| | Branch | Commit | Version | Date |
|---|---|---|---|---|
| **Currently running** | `main` | `77e17529` | `26.6.1-alpha.1506` | 2026-06-14 |
| **Latest available** | `alpha` | `8212374d` | `26.7.26-alpha.227` | 2026-07-26 |
| **Common ancestor** | — | `6a372d2f` "chore(release): bundled cut — codex-killer + #972 partial wire" | — | 2026-05-30 |

Note on versioning: this repo uses CalVer (`vYY.M.D-alpha.N`, documented in `CHANGELOG.md`), so `alpha.227` on `26.7.26` is **not** smaller than `alpha.1506` on `26.6.1` — the counter resets with the date bucket. Don't read the build number as a monotonic count.

## TL;DR

**Risk: MEDIUM. Recommendation: upgrade, but not blind — take a data snapshot first, and verify one thing (federation/peer routes) before you commit.** Six weeks of very active, disciplined development (1176 commits) sit on top of your current build. The MCP tool surface is purely additive (0 removed, 8 new tools), dependency versions are untouched, and the 24 new DB migrations follow a safe additive pattern I verified by reading the SQL. The one real finding that could bite you: **the raw HTTP federation/peer subsystem (TOFU pinning, peer registry, `/api` peer routes) was deleted wholesale in `alpha`**, replaced by a different mechanism (MCP-native bridge tools). If nothing in your fleet talks to this server's old peer HTTP endpoints directly, this is a clean upgrade.

---

## 1. Scale of change

Measured from the true merge-base (`6a372d2f`, 2026-05-30) — NOT a naive `main` vs `alpha` diff, since the two branches **diverged** rather than one being strictly ahead of the other (see §5).

| Direction | Commits |
|---|---|
| `alpha`-only (what you'd gain) | **1176** |
| `main`-only (what only exists on your running branch) | **125** |

| Diff (`6a372d2f..alpha`) | Files | Insertions | Deletions |
|---|---|---|---|
| Raw (`git diff --shortstat`) | 5317 | +196,511 | −13,562 |
| **Excluding committed Rust build artifacts** (see caveat below) | **2348** | **+170,321** | **−13,562** |
| Of which: `src/` (the actual MCP server) | 771 files | — | — |
| Of which: `tests/` (new top-level test dir; `main` has no top-level `tests/`, only scattered `__tests__`) | 1050 files | — | — |

**Caveat on the raw number**: 2,969 of the 5,317 "changed" files (~16% of all changed lines) are under `frontend/src-tauri/target/` — a **compiled Rust/Cargo build-artifact tree for the new Tauri desktop app, committed to git**. `alpha`'s `.gitignore` does not exclude `target/` or `src-tauri/`, so this is dead weight in every future clone/fetch, not meaningful code. Worth a cleanup PR on their side, but it doesn't affect your MCP server's runtime.

**What actually grew** (new top-level directories not in `main` at all): `frontend/` (Tauri desktop app, ~232 real source files + the build junk above), `tests/` (new top-level test suite, 1050 files), `workers/` (3 Cloudflare Workers: `mcp/`, `studio/`, `federation/`), `packages/canvas-plugins/`, `sidecar/turbovec/` (Python vector service), `specs/`, `benchmarks/`, `tools/`. `main`'s equivalent frontend surface was `web/` (an Astro/Cloudflare static site) — CHANGELOG.md confirms this was superseded ("legacy static site stack").

Commit-message shape (`alpha`-only range, keyword hit-counts): `vector` 189, `mcp` 82, `search` 59, `fix` 212, `feat` 399, `migrat` 15, `embed` 21, `schema` 7, `security`/`vuln` 2, `BREAKING` **0**, `renam` **0**.

## 2. Breaking changes

### 2.1 Federation/peer HTTP subsystem: removed (the one to verify before upgrading)

Confirmed by direct source-tree comparison, not just commit messages:

- `main` has an entire peer module: `src/peer/peer-tofu.ts` (TOFU key pinning), `src/peer/peer-registry.ts`, `src/peer/peer-query.ts`, the route `src/routes/peer/peers.ts`, and `src/server/__tests__/peer-identity.test.ts`.
- `alpha` has **zero files matching `*peer*` anywhere under `src/`**.

This matches two commits in `alpha`'s own history: `a0a54929 refactor: remove federation peer routes (#1873)` and `a85744b1 chore: remove UDP scout announcer (#1861)`. It also lines up with `CHANGELOG.md`'s "2026-06-06 alpha wave" section, which shows peer identity endpoints, TOFU pinning, and peer feed/search routes were added via "migration #39" (PR #1353) earlier in `alpha`'s own timeline — i.e., `alpha` built this out and then later tore it down itself.

The likely replacement is a new **always-on MCP-to-MCP bridge**: `oracle_mcp_list_tools` / `oracle_mcp_call` (see §3), which the code comment in `src/config/tool-groups-core.ts:14-23` describes explicitly: *"the local↔remote MCP bridge... a config that turns every group off must still be able to reach a remote Oracle, which is the whole point of the bridge."* Reading between the lines, federation moved from raw HTTP peer routes to first-class MCP tool calls.

**Action before upgrading**: confirm nothing in your Maw/federation tooling calls this server's old `/api/identity`, peer-list, or peer-feed HTTP routes directly. If your federation flows go through `maw` (tmux/Discord) rather than this MCP server's HTTP peer API, you're unaffected.

### 2.2 MCP tool surface: purely additive — good news

Directly diffed `src/config/tool-groups.ts` (main) against `src/config/tool-groups-core.ts` (alpha):

- **0 tools removed.** Every tool name in `main`'s `TOOL_GROUPS` (`oracle_search`, `oracle_read`, `oracle_list`, `oracle_concepts`, `oracle_learn`, `oracle_stats`, `oracle_supersede`, `oracle_handoff`, `oracle_inbox`, `oracle_thread*`, `oracle_trace*`, `oracle_reflect`, `oracle_verify` — 21 tools + the `____IMPORTANT` meta-tool) still exists in `alpha`.
- **8 tools added**: `oracle_ask`, `oracle_search_chain`, `oracle_research_note`, `oracle_profile`, `oracle_recap`, `oracle_trace_distill`, `oracle_mcp_list_tools`, `oracle_mcp_call` (descriptions in §3).
- **1 alias soft-deprecated, not removed**: commit `f2069048 chore(mcp): deprecate the muninn_ tool alias with a warning first (#2827)`. Both versions already normalize `arra_*` and `muninn_*` prefixes to `oracle_*` (`normalizeToolName()` exists in both files, identical logic); `alpha` adds a one-time `warnDeprecatedAliasOnce()` when a caller uses the old prefix. Calls with old prefixes still work — you just get a stderr warning.
- `oracle_search`'s input schema (`src/tools/search.ts` in main vs `src/tools/search/definition.ts` in alpha) kept every existing parameter (`query`, `type`, `limit`, `offset`, `mode`, `project`, `cwd`, `model`) with identical enums/defaults, and only **added** two optional ones: `retrieval` (`full`/`compact-summary`) and `asOf` (bitemporal historical search). No parameter was removed, retyped, or made newly-required.
- A real config-handling bug got fixed along the way: in `main`, `ORACLE_ENABLED_TOOLS` naming only unrecognized tool names silently disabled the **entire** MCP surface (empty allow-list → nothing served). `alpha`'s `tool-groups-core.ts:153-157` explicitly guards against this: *"An allow-list naming ONLY unrecognised tools must not serve zero tools... A filter that matches nothing means 'no usable filter', not 'allow nothing'."* If you rely on `ORACLE_ENABLED_TOOLS`/`ORACLE_DISABLED_TOOLS`, this is a fix, not a break.
- `CHANGELOG.md` line 63 explicitly notes: *"Legacy MCP tool enable/disable toggles are preserved through the manifest loader."* — deliberate backward-compat design goal, not an accident.

### 2.3 HTTP response envelope change (secondary — only matters if you hit the HTTP API directly)

`a502e738 refactor(http): envelope-wrap the 10 schema-bearing route responses (#2821 step 1) (#2841)` — changes the JSON shape of 10 HTTP routes. This is irrelevant if you only talk to this server over the MCP stdio protocol (as Claude Code does); it matters only if some other script/tool in your stack curls this server's `/api/*` routes directly and parses raw response bodies.

### 2.4 Schema/data-directory changes: additive, not breaking (full detail in §6)

- 24 new SQL migrations (`0018`–`0041`), all additive (`ADD COLUMN ... DEFAULT ... NOT NULL` pattern, new tables, new indexes/triggers) — no renamed/dropped columns or tables found.
- `ORACLE_DATA_DIR_NAME` (`.arra-oracle-v2`), `LANCEDB_DIR_NAME` (`lancedb`), `CHROMADB_DIR_NAME` (`.chromadb`), `COLLECTION_NAME` (`oracle_knowledge`) are **byte-identical constants** in both `src/const.ts` files. No directory rename.

### 2.5 Nothing else rose to "breaking"

Grepped the full 1176-commit `alpha`-only log for `BREAKING` (0 hits), `renam` (0 hits, beyond the tool-alias case above), `remov` (3 hits total: the peer/UDP-announcer removal above, plus `3a45142a docs: remove stale route count claim` — a docs-only fix), `deprecat` (1 hit, the tool alias above), `rollback`/`revert` (0 hits).

## 3. Notable new features relevant to an MCP consumer

**New tools** (exact descriptions from source):

| Tool | Description |
|---|---|
| `oracle_ask` | "Ask Oracle for a grounded answer over memory/search. Returns answer, citations, citationIndexes, warnings, noEvidence, search metadata, and sources." — RAG-style Q&A, not just raw hit lists. |
| `oracle_search_chain` | "Run iterative vector search over linked results, expanding from the best hit on each hop." — multi-hop semantic search. |
| `oracle_recap` | "Emit a compact session-start Oracle wake-up context: identity plus top memories by heat/confidence grouped by project." |
| `oracle_research_note` | "Store a Thor Stormforge research/dev artifact as searchable learning memory." |
| `oracle_profile` | "List or read code-backed Oracle profiles such as Thor Oracle / Stormforge." |
| `oracle_trace_distill` | "Distill a trace into a Thor/Stormforge awakening and optionally promote it to learning memory." |
| `oracle_mcp_list_tools` / `oracle_mcp_call` | "MCP-IN: start an external stdio MCP server and list its advertised tools" / "call one tool exposed by an external stdio MCP server." — this server can now proxy into *other* MCP servers. Always-on, can't be disabled by group config. |

**Search/ranking**:
- Bitemporal / valid-time search: `oracle_search`'s new `asOf` parameter + migrations `0031_oracle_documents_valid_time.sql`, `0033_memory_valid_time.sql` — query the knowledge base as it existed at a past point in time.
- Optional reranking: `509f0240 feat(benchmarks): add optional honest recall rerank stage (#2474)`, `23d35293 feat(memory): expose confidence rerank config (#2284)` — opt-in, not a default-on behavior change.
- Confidence honesty: `alpha`'s tip commit itself is `feat(search): a ranking signal with no data now says so, once (#2882)` — the search/ranking work continued right up to HEAD.
- A whole new **memory subsystem**: migrations `0021_add_oracle_memories`, `0036_memory_consolidation`, `0037_memory_tiered_salience`, `0034_memory_ttl` — tiered, decaying, consolidating memory on top of plain documents.

**Multi-tenancy**: migration `0022_tenant_isolation.sql` adds a `tenants` table + `tenant_id` on 6 core tables; `f748fb65 fix(db): harden tenant schema integrity (#2372)` and migration `0032_schema_integrity_guards.sql` (defensive triggers) followed. Not something you asked for, but it's there and it's safe (see §6).

**Embeddings/vector**: `alpha` adds a Gemini embedding provider (`src/vector/providers/gemini.ts`), a new `turbovec` adapter backed by a Python sidecar (`sidecar/turbovec/{server.py,vector_index.py}`), fan-out queries across multiple vector indexes (`src/vector/fan-out.ts`, `fanout-query.ts`), embedding drift benchmarking (`src/vector/drift-benchmark.ts`, `bench:bge-m3-drift` script), and cost estimation (`cost-estimation.ts`). All are additional adapters/providers behind the existing `ORACLE_VECTOR_DB` switch — **`lancedb` is still the hardcoded default** in both `main`'s and `alpha`'s `src/vector/factory.ts`, so none of this is forced on.

**Deployment surfaces** (all new, all opt-in — don't affect your local/stdio setup unless you choose to use them): 3 Cloudflare Workers (`workers/mcp`, `workers/studio`, `workers/federation`, each with its own `wrangler.jsonc` and `package.json`), a Tauri desktop app shell (`frontend/`), a `packages/canvas-plugins` package. `package.json` gained a `"cloudflare": { "bindings": {...} }` block documenting D1/Vectorize/Workers-AI bindings for that deploy target only.

**Docs**: `alpha` ships `docs/DB-MIGRATIONS.md` (migration workflow, quoted in §6), `AGENTS.md`, `DESIGN.md`, `CONTRIBUTING.md` — none of this existed in `main`.

## 4. Bug fixes that matter

From `alpha`'s own commit log (i.e., work you'd gain):
- `f748fb65 fix(db): harden tenant schema integrity (#2372)`
- `c43cae1b fix(db): recover migration index drift (#2383)`, `432fe525 fix(storage): harden migration drift repair (#2334)`, `f26e271c test(storage): tolerate additive migration repairs (#2287)`, `92fb1805 test(db): harden migration edge cases (#2181)` — a whole hardening arc around migration-drift recovery, backed by `src/storage/migration-repair.ts` and two dedicated test files (`tests/storage/partial-migration-repair.test.ts`, `tests/db/migration-drift-recovery.test.ts`).
- `bea1f24e security: tighten HTTP route validation and auth contracts (#1772)`, `8bf91493 Centralize browser security headers in middleware (#1538)`.
- `d3f35e4e fix(indexer): harden reindex vector queue (#2376)`, `8e0fda4f Make vector reindexing visible from the dashboard (#1615)` — `alpha`'s own answer to the reindex-corruption class of bug (see §5 for why I looked for this specifically).

## 5. Branch divergence — read this before treating it as a simple upgrade

This is not "`alpha` = `main` + new stuff." `git merge-base --is-ancestor` fails both directions: **`main` has 125 commits that are not reachable from `alpha`'s current tip**, dated 2026-05-30 → 2026-06-14. Reading the full list (`git log 6a372d2f..main`), the pattern is clear: up to roughly PR #1250s, `main` and `alpha` were kept in sync via repeated "Cut alpha after X" / "Release X as alpha for fleet validation" merge ceremonies (e.g. `19e476f9 Release peer identity pairing as alpha for mawjs validation` immediately preceding `697463bc Add maw peer identity endpoints for federation pairing (#1249)`). **Starting around PR #1366, that sync stopped** — `main`'s remaining ~38 commits (PRs #1366–#1435, through `77e17529` on 2026-06-14) are direct feature/fix work that landed on `main` only, with no corresponding merge back from/to `alpha`.

I did **not** exhaustively verify all 125 main-only commits have equivalent coverage in current `alpha` — that would require a commit-by-commit reconciliation beyond this pass. I did spot-check the two that looked highest-risk to lose:
- `60fac59c Fix vector reindex corruption without dropping LanceDB tables (#1254)` → `alpha` has its own independent hardening here (`d3f35e4e #2376`, `8e0fda4f #1615`), so the class of bug is addressed, even if not by the identical patch.
- `2222f17a Prove zero-config onboarding flow end to end (#1394)` → `alpha` still has `src/integration/zero-config-start.test.ts`, so the capability exists on both sides.

**Recommendation**: treat the 125 main-only commit subjects (saved in this investigation) as a checklist if you depend on anything specific from `main`'s May–June work that isn't an obvious `alpha` theme (vector/MCP-proxy/federation/onboarding — all of which `alpha` clearly kept investing in).

## 6. Data compatibility

**Directory layout — unchanged.** Confirmed identical in both `src/const.ts`: `ORACLE_DATA_DIR_NAME = '.arra-oracle-v2'` (i.e. `~/.arra-oracle-v2`, or `$ORACLE_DATA_DIR` override), `LANCEDB_DIR_NAME = 'lancedb'`, `CHROMADB_DIR_NAME = '.chromadb'`, `COLLECTION_NAME = 'oracle_knowledge'`. (Aside: `docs/DB-MIGRATIONS.md` and the team-lead brief both say `~/.oracle` — that's a pre-existing documentation/code mismatch in **both** versions, not something `alpha` introduces or changes. Whatever the true default really is, it's the same in both checkouts.)

**Vector backend — no change forced.** Both `main` and `alpha`'s `src/vector/factory.ts` default to `'lancedb'` (`ORACLE_VECTOR_DB` env var overrides). `main` already carries both a ChromaDB adapter (legacy) and a LanceDB adapter; `alpha` continues the same pattern and adds `turbovec` (opt-in Python sidecar) and Cloudflare Vectorize (opt-in, edge-only) as further options. Nothing about your default local setup changes here.

**SQL schema (Drizzle/SQLite) — additive, and I read the SQL, not just the filenames.**
- `main` has migrations `0000`–`0017` (18 files). `alpha` has `0000`–`0041` (42 files). **The first 18 filenames are byte-identical** between the two checkouts (same auto-generated slugs, e.g. `0004_warm_mesmero.sql`, `0017_fts5_bootstrap.sql`) — confirming these are the same historical migrations, unmodified, not rewritten.
- I read `0022_tenant_isolation.sql` and `0032_schema_integrity_guards.sql` in full. The tenant migration adds `tenant_id text DEFAULT 'default' NOT NULL` via `ALTER TABLE ... ADD COLUMN` on 6 tables — SQLite backfills existing rows with the default automatically, and Drizzle-generated `INSERT`s from **old** `main` code (which won't mention `tenant_id` at all) will still work because SQLite fills any column absent from an explicit-column-list `INSERT` with its table-level default. The integrity-guards migration only adds indexes and defensive `TRIGGER`s (auto-creates a missing tenant row rather than failing; only `RAISE(ABORT)`s on a genuinely invalid state like a document superseding itself) — nothing here rejects normal old-code writes.
- No `DROP TABLE`, `DROP COLUMN`, or `TRUNCATE` found anywhere in the `alpha`-only commit range.
- `docs/DB-MIGRATIONS.md` (new in `alpha`) documents an explicit CI gate: migrations must "replay from empty state" (`bun db:migrate` against a fresh temp dir) and a fresh DB must `bun db:push` cleanly — both checked before merge. This is a real safety net, not just a claim.
- Migrations run via `bunx drizzle-kit migrate` (a manual `bun db:migrate` step in both versions) — I found no auto-run-on-boot code path in `src/index.ts`/`src/server.ts` in either checkout. You control when migrations execute.

**Practical rollback story**: upgrading `main → alpha` and running the new migrations, then rolling back to `main`'s code, should leave your core documents/search/trace data fully readable — old code simply won't touch the new tables/columns. The one nuance: any data created **through alpha-only tools** (e.g. `oracle_recap`'s memory-heat tracking, `oracle_research_note` entries, non-`default` tenants) would sit dormant and inaccessible via `main`'s tool set until you upgrade again — not lost, just invisible to the older binary.

**Not verified**: I found no evidence of an incompatible LanceDB *table* schema change (as opposed to the SQL side, which I did verify), but I did not exhaustively audit LanceDB's Arrow schema across versions — treat that as an open item. Standard due diligence (back up `~/.arra-oracle-v2` before upgrading) covers this regardless.

## 7. Risk assessment

| Risk | Likelihood | Impact | Notes |
|---|---|---|---|
| Federation/peer HTTP routes gone | Confirmed present | Low–Medium | Only bites you if something calls this server's old `/api` peer routes directly. Verify before upgrading. |
| Lost main-only fix/feature (of the 125) | Low–Medium | Low–Medium | Not exhaustively reconciled; spot-checks (reindex corruption, zero-config onboarding) came back covered. |
| DB migration failure/drift | Low | Medium | Migrations are additive, SQL-verified safe, and explicitly CI-gated for empty-replay; a `migration-repair.ts` self-heal path exists for drift. |
| Vector index incompatibility | Low | Medium | Same default adapter (`lancedb`), same dependency version (`@lancedb/lancedb ^0.27.2` pinned identically in both `package.json`s). |
| MCP tool-call breakage | Very low | High if it happened | 0 tools removed, 0 params removed, tool-alias deprecation is soft (warning only), `@modelcontextprotocol/sdk` version is pinned identical (`^1.29.0`) in both. |
| Dependency/runtime upgrade pain | Very low | Low | Core deps (`drizzle-orm`, `elysia`, `@lancedb/lancedb`, `sqlite-vec`, `better-sqlite3`, `commander`) are the **same version** in both `package.json`s. New deps are scoped to opt-in Cloudflare/Playwright/Tauri surfaces you wouldn't touch just by upgrading the server. `engines.bun >= 1.2.0` unchanged. |
| Reversibility | — | — | Rollback to `main`'s binary after migrating is safe at the schema level (verified via migration SQL). Recommend snapshotting `~/.arra-oracle-v2` (and `~/.chromadb` if present) before upgrading as a zero-cost safety net. |

**Reversibility overall: good.** This is a `git checkout`/redeploy of code plus a one-way-but-safe set of additive SQL migrations — not a destructive data transformation. A file-level backup of the data dir makes it fully reversible.

## 8. Recommendation

**Risk rating: MEDIUM** (would be LOW if not for the confirmed federation/peer-route removal and the un-reconciled 125 main-only commits).

**Go, with two preconditions:**
1. Confirm nothing depends on this server's raw HTTP peer/federation routes (`src/routes/peer/peers.ts` and friends in `main`) before cutting over — check any Maw federation config that might point at this server's `/api` peer endpoints specifically, as opposed to going through tmux/Discord.
2. Snapshot `~/.arra-oracle-v2` (data dir) and `~/.chromadb` (if it exists) before upgrading. Costs nothing, makes the whole thing trivially reversible.

Everything else in this delta — the MCP tool surface, dependency versions, schema migrations, data directory layout — supports a routine upgrade. Six weeks of concentrated work went into search quality (bitemporal search, memory tiering, honest confidence reporting), and none of it was gated behind a change you're forced to adopt (vector backend default unchanged, new deploy targets are opt-in, new tools are additive).
