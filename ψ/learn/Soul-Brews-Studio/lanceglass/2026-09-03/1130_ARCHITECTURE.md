# Lanceglass - Architecture

Source read at: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/`
Version at time of learning: `26.9.1-alpha.1401` (package.json:3)
Thesis, printed in the UI shell itself (`ui/index.html:11`):

> THESIS: Treat agent JSONL as evidence: inspect the source, import bounded work, and preserve provenance.

Lanceglass turns append-only Claude Code / Codex JSONL session logs into a typed, queryable local LanceDB, with an optional (always-explicit) embedding layer on top. This document covers structure, entry points, core abstractions, the local-vs-deployed split, dependencies, and the end-to-end data flow - enough to reimplement it.

---

## 1. Directory structure and organizing philosophy

```
lanceglass/
|-- AGENTS.md, DESIGN.md, PRODUCT.md, README.md, SECURITY.md   # contracts, not just docs (see section 7)
|-- package.json, tsconfig.json, vite.config.ts, wrangler.toml, justfile
|-- docs/
|   |-- embedding-provider-plugins.md      # plugin contract for section 3.8
|   |-- vector-visualization-plugins.md    # plugin contract for the UI's vector map
|   |-- ui-state-gallery.md, lanceglass-architecture.{html,json,png}
|   `-- screenshots/*.png
|-- fixtures/minimal/
|   |-- session.jsonl      # 5 canonical blocks + 1 corrupt line + 1 skipped "progress" line
|   `-- z-session.jsonl    # second file, used to prove multi-file plan/import
|-- lessons/01..08-*.md    # a numbered curriculum - see "organizing philosophy" below
|-- maw-plugin/
|   |-- index.ts           # maw CLI adapter - a process shim, no logic of its own (section 2.4)
|   |-- plugin.json
|   `-- streaming.test.ts
|-- scripts/
|   |-- build-maw-plugin.ts  # packages maw-plugin/dist + writes project-root.txt marker
|   |-- check-version.ts     # enforces package.json / plugin.json version identity
|   `-- smoke.ts             # executable end-to-end spec - see section 8
|-- src/                    # flat - no feature folders, one core implementation
|   |-- types.ts                     # domain row types (EventRow, SourceFileRow, ...)
|   |-- schemas.ts                   # Apache Arrow schemas - the tables' actual shape
|   |-- normalize.ts                 # JSONL record -> EventRow[]/EventSourceRow[] (section 3.2)
|   |-- database.ts / .plain.ts / .vector.ts   # the two-store engine (section 3.1)
|   |-- importer.ts                  # discover/intake/plan/importFile/importSource (section 3.3, 835 lines - largest module)
|   |-- sources.ts                   # source presets (claude/codex/fixture) + root resolution
|   |-- cli.ts                       # CLI entry point (section 2.1)
|   |-- server.ts                    # UI/API server entry point (section 2.2, 879 lines)
|   |-- jobs.ts                      # background import job runner (section 2.2, section 3.6)
|   |-- event-browser.ts / event-view.ts   # Stream-tab read paths (LanceDB-backed vs pure-fn)
|   |-- history.ts                   # History-tab grouping (pure functions over rows)
|   |-- history-vectors.ts           # scope + sample + in-process PCA for the vector map
|   |-- embedding-provider.ts        # EmbeddingSpace/Deployment/Provider primitives (section 3.5)
|   |-- embedding-plugin.ts          # the plugin contract (defineEmbeddingProviderPlugin)
|   |-- embedding-plugins.ts         # registry + the 3 built-in plugin definitions
|   |-- embeddings.ts                # embedPending() orchestrator + public re-exports
|   `-- embedding-providers/
|       `-- cloudflare.ts            # one concrete transport adapter
|-- tests/                  # mirrors src/ file-for-file, not colocated __tests__
|   `-- {embedding-cli,embedding-provider,embeddings,event-browser,event-view,
|         history,history-vectors,importer,jobs,normalize,vector-status}.test.ts
|-- types/
|   |-- bun-runtime.d.ts, bun-test.d.ts   # ambient type shims
|-- ui/                      # an independent Vite/React root (vite.config.ts: root: "./ui")
|   |-- index.html
|   `-- src/
|       |-- App.tsx                  # top-level shell: Events / Import / Jobs (2,486 lines - largest file in repo)
|       |-- HistoryWorkspace.tsx     # the History tab (1,567 lines, second-largest)
|       |-- ProjectCombobox.tsx      # ARIA combobox, Ctrl+K project/oracle picker
|       |-- location.ts (+.test.ts) # URL state (workspace/job/source/project/folder/view)
|       |-- history-date.ts, history-sort.ts, history-source.ts (+ .test.ts siblings)
|       |-- vector-visualization.ts, vector-visualizations.ts (+.test.ts)  # plugin registry (section 3.10)
|       |-- VectorMap3D.tsx (Three.js, lazy) / VectorMap2D.tsx (SVG)       # the two built-in plugins
|       |-- latest-request.ts, job-progress.test.ts, plan-filter.test.ts, event-facets.test.ts
|       |-- main.tsx, index.css, vite-env.d.ts
`-- worker/                  # a SECOND backend for the SAME ui/dist build - see section 4
    |-- index.ts             # Cloudflare Worker: full /api/* contract over synthetic in-memory data
    `-- index.test.ts
```

### Organizing philosophy

**It is a lab, and the directory layout is the curriculum.** `lessons/01-choose-db.md` through `lessons/08-optional-embeddings.md` map almost bijectively onto the build order of `src/`: choose LanceDB -> create the DB -> typed schema+repository boundary -> normalize JSONL -> import+dedupe -> CLI -> UI -> optional embeddings as a *ninth*, deliberately-separate step. `src/` stays flat (only `embedding-providers/` nests) specifically so this progression, and the "one core implementation" invariant, stay visible - `cli.ts` and `server.ts` both import directly from sibling `src/*.ts` files; nothing is hidden behind feature folders.

**Lesson 03 names the pattern directly** (`lessons/03-schema-and-repository.md`):
> This is **ORM-like**, not a full ORM. TypeScript row types describe what application code uses; runtime Arrow schemas describe what LanceDB stores; repositories own table operations. Callers should not scatter raw table names, filters, or row shapes throughout the importer, CLI, and UI.

**`tests/` mirrors `src/` one file at a time** rather than colocating `*.test.ts` next to sources (the UI is the exception - `ui/src/*.test.ts` sit next to what they test). `fixtures/minimal/` holds exactly two tiny synthetic JSONL files, reused by the lessons, `scripts/smoke.ts`, and CI - one canonical fixture, not per-test mocks.

**`ui/` is a fully separate build root**, only ever talking to the server over `/api/*` (proxied in dev via `vite.config.ts:25-29`, same-origin in prod). **`worker/`** is a second, independent deploy target for that same build (section 4). **`maw-plugin/`** is a third distribution channel that adds no logic at all (section 2.4). The repo is organized as *one core + three thin windows onto it* (CLI, server+UI, maw) *plus one fully-mocked public window* (worker).

---

## 2. Entry points

### 2.1 CLI - `src/cli.ts`

Run directly: `bun src/cli.ts <command>` (package.json script `"cli"`, cli.ts:26-27 reads `Bun.argv` with a hand-rolled `--flag value` reader, no argparse dependency).

| Command | Purpose |
|---|---|
| `choose` | Prints the "why LanceDB" decision record (cli.ts:198-211) |
| `init` | Creates the 3 plain tables if missing; reports both store directories |
| `schema` | Dumps `schemaDescription()` (field name : Arrow type per table) |
| `normalize --file <f> [--source fixture]` | Runs normalization only, no DB write - `preview()` |
| `plan [--source ...] [--root ...]` | Exact plan: hash-compares files, prints summary (no `files[]`) |
| `import [--max-files N] [--expect-plan <rev>] [--expect-count <n>]` | The writer |
| `embed providers` \| `embed probe [--deployment ...]` \| `embed run [...]` | Embedding subsystem (section 3.5) |
| `status` | Table counts, per-source counts, vector-store health |
| `events [--source ...] [--limit 20]` | Raw row dump |

`--expect-plan`/`--expect-count` are the plan-revision fencing mechanism described in section 3.3.

### 2.2 UI server - `src/server.ts`

`bun run ui` = `vite build` then `bun src/server.ts` (package.json:22-23); `bun run ui:dev` runs a Vite dev server that proxies `/api` to `127.0.0.1:4320` (vite.config.ts:25-29). The server is one `Bun.serve` instance (server.ts:735-865), hostname pinned to `127.0.0.1`, that additionally **rejects any request whose `Host` header isn't localhost** (`validateLocalHost`, server.ts:641-646) - a DNS-rebinding defense appropriate for a tool that reads private history. It serves the built SPA at `/` and `/assets/*`, and JSON under `/api/*`:

`GET /api/status`, `/api/events`, `/api/events/facets`, `/api/events/live`, `/api/history`, `/api/history/session`, `/api/vectors/visualize`, `/api/import/plan`, `/api/import/intake`, `/api/jobs`, `/api/jobs/:id/log`
`POST /api/import` (synchronous, single-writer-locked via `jobs.tryAcquireSync`), `/api/jobs/import` (async, 202), `/api/jobs/:id/cancel`

There is **no separate "worker" process for background imports** - `JobManager.run()` (`src/jobs.ts:264-360`) literally `Bun.spawn`s `bun src/cli.ts import ...` as a child process per job and streams its stdout/stderr into a capped log ring (section 3.6). The "background job runner" *is* the CLI, invoked again.

### 2.3 Cloudflare demo worker - `worker/index.ts`

A **second backend**, not an entry point to the real system. Deployed via `wrangler.toml` (`main = "worker/index.ts"`, name `lanceglass-fixture-demo`) and reachable at the public URL in README.md: `https://lanceglass-fixture-demo.laris.workers.dev/`. Full treatment in section 4.

### 2.4 maw plugin - `maw-plugin/index.ts`

Registered as maw command `jsonl-scanner` (alias `jscan`, `maw-plugin/plugin.json`). It resolves the real project root - either the dev checkout itself, or (once packaged by `scripts/build-maw-plugin.ts`) a `project-root.txt` marker file written next to the installed plugin pointing back at the source repo (`maw-plugin/index.ts:28-41`) - and then does nothing but `Bun.spawn(["bun","src/cli.ts",...args])` inside that root (or `bun run ui:build` + `bun src/server.ts` for `maw jscan ui`, index.ts:154-166). It owns **zero business logic**: forwarding stdout/stderr, forwarding SIGINT/SIGTERM/AbortSignal to the child, and translating a `--help` subcommand into printed usage. `scripts/build-maw-plugin.ts` refuses to build if `maw-plugin/plugin.json#version` != `package.json#version`.

### 2.5 MCP

**None exists.** No `@modelcontextprotocol` dependency, no MCP server/tool definitions anywhere in the tree (confirmed by search across `src/`, `ui/`, `worker/`, `maw-plugin/`). The only "agent-facing" integration surface is the maw plugin above.

### 2.6 `justfile` recipes (justfile:1-66)

`lesson-01`..`lesson-07` are literal `bun src/cli.ts <cmd>` calls matching the lesson curriculum; `lesson-08` doesn't exist as a recipe (embeddings are covered by the `embed-*` recipes instead). Operational recipes: `archive-plan`, `embed-providers`, `embed-cloudflare-probe`/`-run`, `embed-dual-4090-probe`/`-run`, `embed-both-probe`/`-run`, `smoke`, `ui`.

### 2.7 `package.json` scripts (package.json:20-31)

`cli`, `ui`, `ui:build`, `ui:dev`, `test` (`bun test`), `typecheck` (`tsc --noEmit`), `version:check`, `smoke` (chains `version:check -> typecheck -> ui:build -> test -> scripts/smoke.ts`), `maw:build`, `maw:install`.

---

## 3. Core abstractions

### 3.1 The two physical LanceDB stores

`Database` (`src/database.ts:88-105`) is, in its own comment, *"a deliberately thin container for two physical LanceDB stores"*:

```ts
export class Database {
  private constructor(
    readonly plain: PlainDatabase,
    readonly vector: VectorDatabase,
  ) {}
  static async open(
    plainDirectory = process.env.PLAIN_DB_DIR ?? process.env.DB_DIR ?? DEFAULT_PLAIN_DB_DIR,
    vectorDirectory = process.env.VECTOR_DB_DIR ?? defaultVectorDirectory(plainDirectory),
    vectorSpace: EventVectorSpaceContract = ACTIVE_EVENT_VECTOR_CONTRACT,
  ) { ... }
}
```

> `plain` is the ordinary importer/UI database. `vector` is optional and stays untouched until an explicit embedding or retrieval operation asks for it. Callers must select their store explicitly; there are no forwarding methods such as `database.events()` that could blur this boundary. (database.ts:83-86)

`Database.open()` asserts the two configured directories don't canonicalize to the same real path - resolved through symlinks and even through not-yet-existing ancestors (`canonicalDirectory`, database.ts:52-66) - so `PLAIN_DB_DIR=/x VECTOR_DB_DIR=/x` (or an alias via symlink) fails loudly instead of silently corrupting one store.

Lesson 08 states the rationale directly:

| Store | Default path | Tables | When it may be opened |
|---|---|---|---|
| `database.plain` | `.data/lancedb` | `events`, `event_sources`, `source_files` | every plan/import/UI read |
| `database.vector` | `.data/lancedb.vector[.<space-id>]` | `event_vectors` | only explicit embedding or future semantic search |

> Import must remain a fast, inspectable fact-gathering operation... If a model server is slow, unavailable, or produces malformed output, ordinary import must still complete and remain resumable. Embedding is derived data. It can be rebuilt later from `database.plain`. (lessons/08-optional-embeddings.md)

`AGENTS.md`'s product invariants make this a hard contract, not a suggestion: *"Import writes only to the plain LanceDB store. Embedding is always explicit."* and *"Never mix incompatible embedding spaces in one physical vector store."*

### 3.2 Schemas (Apache Arrow - `src/schemas.ts`)

All fields are non-nullable `Utf8`/`Int32`/`Float64`/`Bool` unless noted. Verbatim field lists:

**`events`** (schemas.ts:43-60) - the canonical row:
`id, event_uuid, block_index(int32), session_id, parent_uuid, timestamp, project, envelope_type, block_type, semantic_role, tool_name, tool_use_id, is_error(bool), text, text_hash, source`

**`event_sources`** (schemas.ts:61-69) - provenance/occurrence:
`id, event_id, source, file_path, file_hash, source_line(int32), observed_text_hash`

**`source_files`** (schemas.ts:70-83) - per-file import manifest / state machine:
`id, source, path, size(f64), mtime_ms(f64), sha256, state, imported_at, parsed_records(int32), inserted_events(int32), duplicate_events(int32), corrupt_lines(int32)`
`state in {pending, imported, requires_reconcile, failed}` (types.ts:75).

**`event_vectors`** (schemas.ts:86-116, lives in the *separate* vector store, created lazily - comment: *"Embeddings intentionally live outside SCHEMAS. Core JSONL imports create only their three ordinary tables; this optional table appears on the first successful embedding batch."*):
`event_id, source, project, session_id, timestamp, text_hash, model, dimension(int32), embedded_at, vector: FixedSizeList<Float32>[dimension]`

Crucially, the table carries **Arrow schema *metadata*** (not just column types) pinning the embedding contract:
```ts
new Map([
  ["embedding_space_id", space.id], ["embedding_provider", space.provider],
  ["embedding_model", space.model], ["embedding_revision", space.revision],
  ["embedding_dimension", String(space.dimension)], ["embedding_distance", space.distance],
  ["embedding_text_policy", space.textPolicy],
])
```
`assertEventVectorContract` (database.vector.ts:59-100) re-verifies *all seven metadata keys, every field name/nullability/type, and the vector's FixedSizeList width + Float32 precision* on **every** table open, throwing a `vectorContractError` on any drift. This is the actual enforcement mechanism behind "never mix incompatible embedding spaces" - not documentation, a runtime assertion.

Active values (schemas.ts:22-28): `EMBEDDING_MODEL = "bge-m3"`, `EMBEDDING_DIMENSION = 1024`, `EMBEDDING_SPACE_ID = "ollama-bge-m3-790764642607-1024-cosine-text-v1"`, `EMBEDDING_TEXT_POLICY = "event.text.slice(0,2000)@v1"`.

### 3.3 The canonical ID scheme (`src/normalize.ts`)

| Identity | Formula | Role |
|---|---|---|
| `event_uuid` | Claude: `record.uuid` else `hash:sha256(stable({sessionId,timestamp,type,parentUuid,message,summary}))`. Codex: `payload.id` else `hash:sha256(stable({sessionId,timestamp,ordinal,payloadType,callId}))` | Identifies one source envelope/turn |
| `id` (events PK) | `` `${event_uuid}#${block_index}` `` (normalize.ts:291) | One canonical row per **content block** inside an envelope |
| `id` (event_sources PK) | `sha256([event.id, source, file_path, line, event.text_hash].join("\0"))` (normalize.ts:310-318) | One row per **observation** of a canonical event at a specific file+line |
| `id` (source_files PK) | `sha256(`${source}\0${path}`)` (importer.ts:190) | One row per (source, absolute path) |
| `text_hash` | `sha256(block.text)` over the *stored* (4,000-char-truncated) text (normalize.ts:289,304) | Change detection for the canonical row - distinct from the embedding pipeline's own hash over its own (2,000-char) truncation |

`stable()` (normalize.ts:8-15) is a deterministic JSON stringifier (recursively key-sorted) so fallback-hash inputs never depend on source object key order.

Codex's ordinal trick (normalize.ts:174-180, 272): the JSONL line number is threaded in out-of-band as `__ordinal` on a shallow-cloned record specifically *"so fallback IDs remain independent of object key ordering while the persisted source record stays untouched."*

Session-identity nuance, Codex only (normalize.ts:149-163) - a rollout file can carry two `session_meta` records; a small state machine (`sessionIdentity: "fallback"|"session_id"|"id"`) guarantees the strong `payload.id` wins permanently over a later legacy `payload.session_id`:
> A rollout may contain a second compatibility session_meta record. The first payload.id identifies the file/rollout, so do not replace it with the later payload.session_id.

`events` rows are written via `mergeInsert("id").whenNotMatchedInsertAll()` (database.plain.ts:76) - this is what makes the whole scheme idempotent: re-importing the same file (or the same event re-observed from a different file) is a merge, not a duplicate insert; `event_sources` gets a genuinely new occurrence row instead.

### 3.4 JSONL -> rows (`src/normalize.ts`)

Two source dialects, one output shape (`EventRow`), two extraction functions:

- **Claude Code** - `extractBlocks()` (normalize.ts:77-138) reads `record.type in {user, assistant, summary}` and `record.message.content` (string, or a content-block array). Classifies each kept block into `semantic_role`: `text->human_intent|assistant_answer`, `tool_use->tool_action`, `tool_result->tool_evidence`, `summary->summary`. Explicitly drops non-text content: *"progress, thinking and images are not search documents"* (normalize.ts:136).
- **Codex** - `codexBlocks()` (normalize.ts:140-256) reads envelope types `session_meta`/`turn_context` (bookkeeping only - cwd/session, no event rows) and `response_item` payloads of type `message`, `custom_tool_call(_output)`, `function_call(_output)`, mapped onto the same five semantic roles.

Both converge in `normalize()` (normalize.ts:258-327), the single place that stamps `id`/`text_hash`/`project` (`basename(cwd)`) and builds each block's paired `EventSourceRow`.

### 3.5 Import / dedupe engine (`src/importer.ts`)

Four public operations, increasing in cost:

1. **`discover`** (importer.ts:174-208) - recursive `*.jsonl` walk, skips `journal.jsonl`, returns `{id,source,path,size,mtimeMs}[]` sorted by path.
2. **`intake`** (importer.ts:210-254) - metadata-only: compares discovered files against the `source_files` manifest by size/mtime alone (no hashing, no LanceDB write). This is the UI's 30-second live-poll endpoint (`/api/import/intake`).
3. **`plan`** (importer.ts:256-340) - exact: hashes file content (unless `compareMode:"metadata"`), classifies each file `new|changed|unchanged|shrunk`, and computes a deterministic `plan_revision = sha256(JSON.stringify([source, root, ...sorted (id,size,mtime,state) tuples]))` (importer.ts:313-325).
4. **`importSource`/`importSourceUnlocked`** (importer.ts:574-804) - the writer.

Safety mechanisms worth reimplementing exactly:

- **Byte-exact snapshot before parsing** (`snapshotFile`, importer.ts:84-172): buffers in memory under 16MiB (`MEMORY_SNAPSHOT_LIMIT`), otherwise streams to a `mkdtemp` file - always to *the exact byte length observed during planning*. A live Claude/Codex session appending to the same file mid-import cannot have its in-flight tail parsed; the new bytes simply reappear as "changed" on the next pass. This is the concrete mechanism behind DESIGN.md's *"Live Claude/Codex JSONL may append between inspection and worker startup... Per-file prefix snapshots and shrink detection remain the write-safety boundary."*
- **Two-pass large-file import** (`importFile`, importer.ts:342-495, used above `MEMORY_SNAPSHOT_LIMIT`): pass one computes a full audit (parsed/blocks/inserted/duplicates/corrupt counts) against a **throwaway temporary LanceDB** opened under `mkdtemp` (`auditDb`), so exact merge-insert dedupe counts are known without holding every ID in memory; the `source_files` row is written `state:"pending"` only after pass one. Pass two re-parses and performs the real write, flipping the row to `state:"imported"` only once fully flushed. A crash between passes leaves a `"pending"` manifest row that a retried import recognizes (`recovery` branch, importer.ts:381-385,433-439,665-694) and *replays deterministically* rather than re-auditing.
- **Cross-file batching for small files** (importer.ts:44-48, 574-794): files <=16MiB are fully parsed into memory (`prepareSmallFile`) and buffered; the buffer flushes to LanceDB at 16MiB total, 5,000 rows, or 256 files (`CROSS_FILE_BATCH_LIMIT`/`CROSS_FILE_ROW_LIMIT`/`CROSS_FILE_FILE_LIMIT`) - so a directory of many small sessions doesn't do one LanceDB write per file. If a later file in a buffered group fails, the already-parsed prefix is flushed first so retry resumes at the failure boundary (comment, importer.ts:768-772).
- **Advisory hard-link file lock** (`acquireImportLock`, importer.ts:56-82, mirrored for embeddings in embeddings.ts:288-321): write a unique candidate file, then `link()` it to the stable lock path - atomic even on filesystems without atomic create-exclusive semantics. A second concurrent writer against the same plain store fails immediately, naming the owning PID.
- **Plan-revision fencing** - `expectedPlanRevision`/`expectedWillParse` (importer.ts:580-598) let a caller pin an import to the exact plan it already showed a human. If the directory drifted underneath (files changed since the plan was shown), import refuses rather than silently importing something unconfirmed. `jobs.ts` re-plans fresh inside the spawned CLI child before writing (the `planPolicy: "exact"|"refresh"` distinction, jobs.ts:272-283 - `"refresh"` is used only for the always-live intake fast path).
- **`maxFiles` bounding + partial reporting** - `ImportReport.partial`/`remaining_files` are how "Import next N" vs "Import all" share one code path against the same underlying `importSource` call.

### 3.6 Chunking / blocking - three unrelated senses

The word is overloaded across the codebase; a reimplementer should keep these separate:

1. **Content blocking** (semantic) - one JSONL line -> *N* `Block`s (normalize.ts `Block` type) -> *N* `EventRow`s, addressed by `block_index`. A single assistant turn with a text answer + a tool call is two blocks, two canonical events, one `event_uuid`.
2. **Write/scan batching** (storage-bounding) - LanceDB write buffers flush every 5,000 rows within one large file (importer.ts:430,485) and at 16MiB/5,000-rows/256-files across small files (importer.ts:44-47,774-779); ID-list lookups are chunked to 256 items per generated `IN (...)` SQL predicate (database.vector.ts:154,179 `for (...; offset += 256)`; server.ts `EVENT_ID_CHUNK_SIZE = 500`, server.ts:43,254-260) to keep query strings and result sets bounded.
3. **Embedding batching** (provider-bounding) - candidates are paged 256-at-a-time from the plain store (`EMBEDDING_PAGE_SIZE`, embeddings.ts:66,342) and sent to the embedding transport in batches of `--batch-size` (default 8, embeddings.ts:64,425-448) - sized for HTTP request/latency limits, independent of the storage batching above.

### 3.7 Read-side abstractions

- **`event-browser.ts`** (`loadEventPage`/`loadEventFacets`) - the Stream tab's query path. `latestExact` (database.plain.ts:131-213) finds the k-most-recent rows via an in-memory binary max-heap over a *streamed* scalar scan (id/source/timestamp only), then fetches full rows only for that page - avoiding a full-table sort on every poll. Facets are cached per `(source,project)` keyed by a cheap `${eventCount}:${occurrenceCount}` revision string (event-browser.ts:84-107), not a real change feed.
- **`event-view.ts`** (`buildEventView`) - a pure, fully in-memory equivalent of the same shape, used by tests and the worker demo (no LanceDB).
- **`history.ts`** (`buildHistory`/`buildHistorySession`) - pure functions over already-fetched rows. Groups by `Asia/Bangkok` calendar day (`Intl.DateTimeFormat`, not UTC-truncation) -> `(source,project,folder)` -> session, and computes `continues_before`/`continues_after` from a session's *full* first/last-seen date span so the UI can show continuation without loading out-of-range days.
- **`history-vectors.ts`** (`visualizeHistoryVectors`) - exact-scopes eligible events (source+project+session_id+day+actor role+folder provenance), evenly samples to `limit` (`evenlySample`), then runs its own from-scratch power-iteration PCA down to 3 axes (`normalizedAxes`, history-vectors.ts:175-249; a seeded linear-congruential PRNG makes the projection deterministic across runs) with a 5th/95th-percentile clip to `[-1,1]` per axis. No external linear-algebra dependency.

### 3.8 Embedding subsystem

Layered contracts, outer to inner:

- **`EmbeddingSpace`** (embedding-provider.ts:25-35) - the identity contract: `id, provider, model, revision, dimension, distance, textPolicy`. *"Stable storage identity. Never reuse this ID for a changed contract."* `defineEmbeddingSpace` validates non-empty fields and an `[a-z0-9][a-z0-9._-]*` id charset.
- **`EmbeddingDeployment`** (embedding-provider.ts:148-181) - a named, concrete instance (space + transport config + `vectorStoreKey`, which defaults to the space id and decides which physical `.vector[.<key>]` directory it writes to). `m5-ollama` and `dual-4090` share `ACTIVE_EVENT_VECTOR_CONTRACT`/`DUAL_4090_EMBEDDING_SPACE` - literally the same frozen object (embedding-provider.ts:78, comment: *"Verified identical to M5 Ollama; deployment hardware is not a vector space"*) - so they safely share one store; Cloudflare's managed model gets an isolated store (`CLOUDFLARE_EMBEDDING_SPACE`) even though it targets the same nominal model family, because its output isn't provably identical.
- **`EmbeddingProviderPlugin`** (embedding-plugin.ts) - *"Public source-plugin seam. A plugin owns transport/configuration; the core continues to own candidate selection, validation, persistence, and resume. Plugins are statically registered and reviewed-never downloaded at runtime."* Three built-ins in `BUILTIN_EMBEDDING_PROVIDER_PLUGINS` (embedding-plugins.ts): `m5-ollama` (single local endpoint), `dual-4090` (round-robin/failover pool over N Ollama endpoints, sharding a batch across endpoints and retrying on any endpoint on failure - embedding-provider.ts:364-427), `cloudflare` (native Workers AI REST - `src/embedding-providers/cloudflare.ts`).
- **Revision pinning, two different mechanisms** because the transports offer different guarantees: Ollama exposes a real model digest, checked against `GET /api/tags` before first use (`verifyOllamaEndpoint`, embedding-provider.ts:266-293); Cloudflare Workers AI exposes **no** digest, so the adapter instead sends one fixed probe string (`CLOUDFLARE_REVISION_PROBE_TEXT`), SHA-256-fingerprints the returned `Float32` bytes, and refuses to run on a mismatch against a fingerprint pinned in source (`verifyRevisionProbe`, cloudflare.ts:53-73,160-169) - *"Workers AI can produce tiny batch-shape-dependent floating-point differences for the same text. The pinned fingerprint was stable across repeated independent probes."* (docs/embedding-provider-plugins.md)
- **`embedPending()`** (embeddings.ts:323-474) - the orchestrator. Takes the hard-link advisory lock (section 3.5) scoped to `<vector-dir>.event_vectors.lock`; pages only `EMBEDDING_ROLES = [human_intent, summary, assistant_answer]` from the plain store (`tool_action`/`tool_evidence` are never embedded - `ROLE_PRIORITY > 2` is filtered out, embeddings.ts:123-129,175-185); for each candidate compares the *existing* vector row's `text_hash`+`model`+`dimension`+`source`+`project`+`session_id`+`timestamp` against the current event and re-embeds only on drift (embeddings.ts:381-399) - naturally incremental, resumable, and self-healing if an event's copied scope metadata is later corrected.

### 3.9 Job orchestration (`src/jobs.ts`)

`JobManager` is an in-process single-writer scheduler: one `writerOwner` slot shared between the synchronous `/api/import` path (`tryAcquireSync`/`releaseSync`) and the async `/api/jobs/import` path, so the UI can never have two writers racing the same plain store regardless of which endpoint triggered them. `run()` spawns `[process.execPath, "src/cli.ts", "import", --root, --source, (--expect-plan/--expect-count | nothing), --max-files?]` as a real child process (jobs.ts:264-299) and tees its stdout/stderr into a capped ring (500 lines, 64KB/line - `MAX_LOG_LINES`/`MAX_LINE_BYTES`) that `/api/jobs/:id/log?from=N` serves by absolute offset. This buffer - not a bespoke progress protocol - is what DESIGN.md calls **"The CLI Is the Evidence Rule"**: *"The browser does not invent progress; it shows the same fixed-argument CLI process and structured completion report as maw."* Cancellation sends `SIGTERM` then `SIGKILL` after a 1.5s grace window (`KILL_GRACE_MS`).

### 3.10 Vector-visualization plugin boundary (`ui/src/vector-visualizations.ts`)

This is the UI-side mirror of the embedding-provider plugin seam in section 3.8, and DESIGN.md names it as an explicit architectural rule: *"Visualizers cross a typed, declarative plugin boundary... The host owns data, vector-space separation, configuration, selection, errors, and the shared roving-tabindex evidence list; a plugin only renders the supplied points and emits a stable `event_id`. New visualizers can be registered without changing the History workspace."* (DESIGN.md, History Workspace section)

`docs/vector-visualization-plugins.md` gives the contract verbatim:
```ts
type VectorVisualizationPlugin = {
  id: string; label: string; description: string;
  dimension: 2 | 3;
  defaultConfig: Readonly<Record<string, boolean | number | string>>;
  configControls: readonly VectorVisualizationConfigControl[];
  load(): Promise<{ default: ComponentType<VectorVisualizationProps> }>;
};
type VectorVisualizationProps = {
  points: readonly VectorVisualizationPoint[];
  selectedEventId: string; onSelect(eventId: string): void;
  config?: VectorVisualizationConfig; onConfigChange?(config: VectorVisualizationConfig): void;
  reducedMotion?: boolean; onUnavailable?(reason: string): void;
  ariaLabel?: string; className?: string;
};
```
`load()` is the lazy-import boundary (so a heavy rendering engine only downloads when its visualizer is actually selected). Host-owned invariants (docs/vector-visualization-plugins.md), each mapping onto a concrete piece of `history-vectors.ts`/`HistoryWorkspace.tsx` behavior already described in section 3.7: fetch each embedding deployment from its own LanceDB directory; never overlay or compare coordinates across incompatible spaces; apply Human/Agent actor filters before coverage, sampling, and PCA; coordinate panels only by stable `event_id` (never by screen coordinates); keep the evidence list as the keyboard-equivalent interface; catch plugin failures so `Atlas 3D` falls back to `Flat 2D` inside the same provider panel, *never* to another embedding provider.

Two built-ins are registered in `VECTOR_VISUALIZATIONS` (`ui/src/vector-visualizations.ts`): `Atlas 3D` (id `3d`, Three.js, lazy-loaded, with optional motion-aware spin) and `Flat 2D` (id `2d`, plain SVG, the always-available fallback) - `VectorMap3D.tsx` and `VectorMap2D.tsx` respectively. IDs are kept stable once shipped because they round-trip through History's URL state (`ui/src/location.ts`).

---

## 4. The local-vs-deployed boundary (`worker/` vs `src/server.ts`)

Two backends serve **the exact same compiled `ui/dist` SPA**; only the server-shaped code differs.

**Local (real):** `bun run ui` -> `vite build` then `bun src/server.ts`. Opens a real `Database` against local LanceDB directories, spawns real `bun src/cli.ts import` child processes, reads real `~/.claude/projects` / `~/.codex/sessions` JSONL. Bound to `127.0.0.1` with a Host-header check (section 2.2) - a single-user local tool, never multi-tenant.

**Deployed (mocked):** `worker/index.ts`, shipped by `wrangler.toml` as the Cloudflare Worker `lanceglass-fixture-demo`. Its `[assets]` binding points at the same `ui/dist` (`wrangler.toml:5-8`); `run_worker_first = ["/api/*","/health"]` routes only those paths to the Worker script, everything else falls through to the static asset binding - `env.ASSETS.fetch(request)` (worker/index.ts:241). The Worker script **fully reimplements the `/api/*` contract** (status, events, facets, live, history, history/session, vectors/visualize, import/plan, import/intake, jobs, jobs/log, jobs/import, jobs/cancel) against **1,000 synthetic rows generated once at module load** (`events`, worker/index.ts:25-45, seeded from a fixed `COPY[]` array of lines and a fixed `EVENT_DATES` range ending 2026-09-01) plus 36 synthetic `files`. There is no KV/D1/R2/Durable Object binding anywhere - `POST /api/import` and `POST /api/jobs/import` just echo a canned `report`/`job` object (worker/index.ts:237-238) rather than mutating anything, and `POST /api/jobs/:id/cancel` always 409s: *"Static demo jobs are immutable."*

`worker/index.test.ts` asserts this boundary as a contract, not an accident:
```ts
expect(health).toMatchObject({ mode: "static-fixture", storage: "none" });
expect(statusResponse.headers.get("cache-control")).toBe("no-store");
expect(status.demo).toEqual({ enabled: true, label: "Static fixture demo", storage: "none", persistence: "none" });
```

README.md states the why directly: *"the production React UI with 1,000 bundled synthetic events. It uses no KV, no D1, no database binding, and no persistence; import actions are deterministic simulations that reset to the same fixture state."* The point isn't merely policy - a tool whose entire purpose is reading a user's *private* local agent history can be given a fully-interactive public demo only because the deployed variant has **no filesystem or storage access to misuse**, structurally, not by promise.

**Where `maw-plugin/` fits on this spectrum:** unlike `worker/`, it reimplements *nothing* - it is a pure process-forwarding shim to the same `src/cli.ts`/`src/server.ts` used locally (section 2.4). So the repo has three deployment shapes on one axis:

```
maw-plugin            local server (src/server.ts)         Cloudflare worker (worker/index.ts)
100% shared code,  ->  100% shared code,                 ->  UI build shared, backend
different launcher     real local LanceDB + real files      fully mocked, zero storage
```

---

## 5. Dependencies

- **Runtime:** Bun >=1.3 (CI pins `1.3.14`, `.github/workflows/ci.yml:19`) as the sole JS runtime - no Node, no separate transpile step; `.ts` files run directly. `"type": "module"` throughout.
- **`@lancedb/lancedb@0.27.2` + `apache-arrow@18.1.0`** - LanceDB is used as an **embedded native Bun/Node addon**: a real columnar database file on local disk, opened in-process via `lancedb.connect(directory)`. It is **not** a Python sidecar and **not** a client/server database - there is no Python anywhere in this repo (no `.py`, no `pyproject.toml`/`requirements.txt`). Table schemas are literal `apache-arrow` `Schema`/`Field` objects (`src/schemas.ts`) - the "explicit Arrow schemas" decision criterion from `lessons/01-choose-db.md`.
- **UI:** `react`/`react-dom@19.2`, `three@0.185` (for the lazy-loaded `Atlas 3D` vector visualizer only), Tailwind v4 via `@tailwindcss/vite` (the Play-CDN-free, Vite-native path), IBM Plex Mono/Sans via `@fontsource*`. No state-management or router library - `ui/src/location.ts` hand-rolls URL state, `App.tsx` hand-rolls the top-level Events/Import/Jobs/History view switch.
- **Embedding model:** **BGE-M3** - `bge-m3` on Ollama, `@cf/baai/bge-m3` on Cloudflare Workers AI - 1,024 dimensions, cosine distance, input = first 2,000 characters of event text (`EMBEDDING_TEXT_POLICY = "event.text.slice(0,2000)@v1"`). **No embedding model ships in-process** - it is always an external HTTP call: a local Ollama daemon, a LAN pool of Ollama daemons (round-robin/failover), or Cloudflare's managed inference endpoint.
- **Dev tooling:** TypeScript `^7.0.2` used only for `tsc --noEmit` (Bun executes directly); Vite `^8.2.2` builds the UI only.
- **No search-index / ANN dependency of any kind** (no FAISS, no HNSW library, no `.search()`/`vectorSearch()`/`createIndex()` call anywhere in `src/`) - see section 6's callout.

---

## 6. End-to-end data flow

```
~/.claude/projects/**/*.jsonl   (or ~/.codex/sessions, or fixtures/minimal)
        |  recursive fs walk, skips journal.jsonl           [importer.ts: discover()]
        v
FilePlan[] {id, source, path, size, mtimeMs}
        |  compare vs source_files manifest (metadata-only, or full sha256)   [plan()]
        v
PlanReport {new, changed, unchanged, shrunk, plan_revision, files[]}   -- shown in the UI's read-only Inspect-plan modal
        |  operator confirms "Import next N" / "Import all"     [POST /api/jobs/import -> JobManager.start]
        v
Bun.spawn(["bun","src/cli.ts","import",...])    -- the SAME child process a terminal user would run   [jobs.ts]
        |  byte-exact snapshot of each selected file's confirmed length      [snapshotFile]
        v
JSON.parse each line -> normalize(record, ctx, state)     [normalize.ts: Claude vs. Codex branches]
        |  -> EventRow[] (one per content block, canonical) + EventSourceRow[] (provenance)
        v
db.plain: events.mergeInsert("id")  +  event_sources.mergeInsert("id")  +  source_files.mergeInsert("id")
        |  idempotent; source_files.state: pending -> imported
        |
        |-----------------------------+
        v                             v
  read paths, no vector store   optional, explicit-only derived path
  /api/events                   `embed run`: page human_intent/summary/assistant_answer
  /api/events/facets            rows from db.plain -> diff text_hash/model/dimension/scope
  /api/history                  against event_vectors -> call Ollama or Cloudflare ->
  /api/history/session          upsert db.vector.event_vectors        [embeddings.ts embedPending]
  [event-browser.ts, history.ts]
        |                             |
        v                             v
  ui/src App.tsx / HistoryWorkspace.tsx     /api/vectors/visualize  [history-vectors.ts]:
  render Stream rows, History calendar      exact-scope eligible events -> sample <=500 ->
                                             in-process 3-axis PCA -> {points:[{event_id,x,y,z,...}]}
                                                         |
                                                         v
                                     HistoryWorkspace.tsx -> VectorMap3D.tsx (Three.js)
                                                        or VectorMap2D.tsx (SVG fallback)
```

**"-> search results" does not fully exist yet, by design, not by omission.** A search of the codebase confirms there is **no free-text or ANN query endpoint anywhere** - the vector store is read only via `metadataForEventIds`/`rowsForEventIds` (exact ID lookups keyed off events already selected by scalar scope), never a nearest-neighbor query; `createIndex`/`IvfPq`/`Hnsw` appear nowhere. `types.ts:42` even leaves the intent as a comment on why scope columns are copied into `event_vectors`: *"Scalar scope metadata is deliberately copied into the vector store so a later ANN query can pre-filter without joining across physical databases"* - "later," not yet built. Today's two search-shaped surfaces are (1) the Stream tab's scalar filters (source/project/folder, exact match) and (2) the History vector map, which **visualizes/clusters** one already-scoped session's embeddings rather than searching across the corpus. DESIGN.md's own wording - *"only explicit embedding or future semantic search"* - frames this the same way: the provider abstraction, dimension/model contract, and physical-store isolation are fully built; the query layer on top is intentionally not.

---

## 7. Verification architecture (how the contracts are enforced, not just documented)

`AGENTS.md` names the required gate:
```bash
bun run smoke   # version:check -> typecheck -> ui:build -> test -> scripts/smoke.ts
```
`scripts/smoke.ts` is not a toy - it is a 9-phase, ~315-line **executable specification** of the entire system, run against a fresh temporary DB directory and a live `src/server.ts` instance on a PID-derived port: it exercises `choose`/`init`/`schema`/`normalize` via the CLI; proves `plan`->partial `import --max-files 1`->resume->repeat is idempotent (asserts exact row counts at each step); proves the maw-plugin shim (`maw-plugin/index.ts`) forwards stdout/stderr identically to the raw CLI; proves the async `/api/jobs/import` path reaches the same result as the synchronous `/api/import` path; proves ordinary import **never creates the vector directory** (`check((await stat(VECTOR_DB_DIR).catch(() => null)) === null, ...)`); and finally serves the production build and asserts the THESIS string survives the Vite build. CI (`.github/workflows/ci.yml`) runs exactly this one job on every push/PR. This is the mechanism that keeps "the browser, direct CLI, and maw adapter on the same core implementation" true over time rather than aspirational.

`scripts/check-version.ts` (invoked as `bun run version:check`) is the second enforced contract from `AGENTS.md`: *"`package.json#version` is authoritative and uses `YY.M.D[-alpha.HMM|-beta.HMM]` in the `Asia/Bangkok` calendar. `maw-plugin/plugin.json` must carry the same version."* - e.g. this snapshot's `26.9.1-alpha.1401` = 2026-09-01, build 14:01 Bangkok time.
