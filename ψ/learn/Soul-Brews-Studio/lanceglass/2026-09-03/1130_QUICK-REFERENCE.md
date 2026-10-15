# Lanceglass - Operator's Quick Reference

Source read: `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/`
Version at read time: `26.9.1-alpha.1401` | License: MIT | Runtime: Bun | DB: LanceDB 0.27.2 / Apache Arrow 18.1.0
Public read-only demo: https://lanceglass-fixture-demo.laris.workers.dev/

This is a practical, copy-pasteable operator's manual. Everything below was
verified by reading source (`src/`, `ui/`, `scripts/`, `justfile`,
`package.json`, `docs/`, `lessons/`), not by executing commands against the
live repo (to avoid mutating it - see "Note on verification" at the end).

---

## Table of contents

1. What it does
2. Architecture in one paragraph
3. Install and quick start
4. Everyday command cheat sheet
5. Every `just` recipe
6. Every `package.json` script
7. CLI reference (every command, every flag)
8. HTTP API reference (what the UI actually calls)
9. Every env var / config knob
10. UI screens, workspace by workspace
11. Configuration: default roots, default data dirs, how to point elsewhere
12. Optional embeddings, in depth
13. Optional `maw` adapter
14. Teardown / reset paths
15. Known limits, caveats, and things that do not work
16. Lessons 01-08, summarized (the author's own recorded findings)
17. Project map

---

## 1. What it does

Lanceglass turns append-only Claude Code / Codex JSONL session logs into a
typed, inspectable local LanceDB database. Quoting the README's framing
directly:

> Lanceglass turns append-only agent session logs into a typed, inspectable
> LanceDB. It detects new and changed JSONL files, imports idempotently,
> preserves provenance, reconstructs work history, and can build optional
> embedding spaces without coupling vectors to ingestion.

Concretely, it is three things wrapped around one shared TypeScript core
(`src/`):

- A **CLI** (`bun src/cli.ts ...`) for scripting/inspection.
- A **local web app** (React 19 + Tailwind 4, served by a Bun HTTP server on
  `127.0.0.1`) for browsing the same data.
- An optional **`maw` plugin adapter** (`maw jscan ...`) that shells out to the
  same CLI/server, so none of the importer logic is duplicated.

Design intent (from `PRODUCT.md`): the primary user is a developer who wants
raw agent JSONL to become a typed, inspectable database, and who needs to see
each import decision (what is new, what is already known, what remains)
*before* trusting it. It is explicitly **not** a production multi-user service
and **not** a relational ORM - it is "smoke-first local tool."

Everything is local-first: no telemetry, no automatic network upload, no
implicit calls to any embedding service. The bundled fixture (`fixtures/minimal`)
proves the entire pipeline without ever touching your real `~/.claude` or
`~/.codex` history.

## 2. Architecture in one paragraph

Two separate physical LanceDB directories, never one:

- **Plain store** (`.data/lancedb` by default) holds `events`, `event_sources`,
  and `source_files`. Every plan/import/UI read touches only this store.
- **Vector store** (`.data/lancedb.vector[.<space-id>]`) holds `event_vectors`.
  It is opened only by an explicit `embed` command or the History workspace's
  vector inspector - **never** by plan/import. Import contacts no embedding
  service, ever.

Each incompatible embedding contract (model, revision, dimension, distance,
text policy) gets its own physical vector directory, keyed by an
`EmbeddingSpace.id`. Mixing spaces in one store is a hard error at write time
(`assertProviderContract` in `src/embeddings.ts`).

## 3. Install and quick start

**Prerequisites:** [Bun](https://bun.sh) 1.3 or newer. `just` is convenient
but optional (every recipe is one `bun` command underneath). `maw` is optional.
No Python, no separate LanceDB server, no `uv` - LanceDB is an embedded
Node/Bun native library (`@lancedb/lancedb`), not a service you run.

```bash
git clone https://github.com/Soul-Brews-Studio/lanceglass.git
cd lanceglass
bun install --frozen-lockfile
bun run smoke
```

`bun run smoke` is the single command that proves the whole system works. It
builds the production UI, creates an isolated temp LanceDB (never touches
`.data/`), normalizes only the bundled fixtures, imports a partial batch,
resumes over HTTP, proves idempotency, checks the plain/vector store boundary,
and serves the built app - 9 numbered phases, ending with a line like:

```
SMOKE PASS - events=7 - partial_remaining=1->0 - repeat_inserted=0 - db=/tmp/lanceglass-smoke-XXXXXX/lancedb
```

(README states this currently covers 163 focused tests plus the nine-stage
fixture run.)

Start the local app for real use:

```bash
bun run ui
# -> http://127.0.0.1:4320
```

`bun run ui` = `vite build` (production UI build) then `bun src/server.ts`.
There is no separate "start" step; the server serves the built `ui/dist` and
the API from one process.

## 4. Everyday command cheat sheet

The handful of commands you actually run day to day, against your **real**
Claude Code history (default source, no flags needed):

```bash
# See what's new without touching the database
bun src/cli.ts plan

# Import a bounded, safe batch (repeat until remaining_files hits 0)
bun src/cli.ts import --max-files 10

# See what's stored
bun src/cli.ts status
bun src/cli.ts events --limit 20

# Same, for Codex instead of Claude Code
bun src/cli.ts plan --source codex
bun src/cli.ts import --source codex --max-files 10

# Browse it
bun run ui   # http://127.0.0.1:4320
```

Always safe to run repeatedly: `plan` writes nothing; `import` is idempotent
(stable event/provenance/file IDs mean a retry never duplicates rows).

## 5. Every `just` recipe

From `justfile` (`root := justfile_directory()`, `fixture := root / "fixtures/minimal"`):

| Recipe | Command it runs | When you'd use it |
| --- | --- | --- |
| `just lesson-01` | `bun src/cli.ts choose` | Print the DB choice rationale (LanceDB vs relational). |
| `just lesson-02` | `bun install --silent` then `bun src/cli.ts init` | Fresh install + create the 3 plain tables. |
| `just lesson-03` | `bun src/cli.ts schema` | Print the Arrow schema description for all 3 tables. |
| `just lesson-04` | `bun src/cli.ts normalize --file "fixtures/minimal/session.jsonl" --source fixture` | Preview normalization of one JSONL file with no DB write. |
| `just lesson-05` | `plan` then `import --max-files 1` against the fixture | See the new-vs-known / partial-import cycle. |
| `just lesson-06` | `status` then `events --source fixture --limit 10` | Inspect what got stored via the CLI. |
| `just lesson-07` | `bun run ui` | Launch the local web app. |
| `just archive-plan path="$HOME/agent-jsonl-backup"` | `plan --root <path> --source archive` | Read-only plan against an arbitrary backup directory (source label `archive`). |
| `just embed-providers` | `embed providers` | List embedding deployments and which env vars are missing. |
| `just embed-cloudflare-probe` | `embed probe --deployment cloudflare` | Connectivity/model-revision check for Cloudflare, no LanceDB opened. |
| `just embed-cloudflare-run limit="20" batch_size="8" source="claude"` | `embed run --deployment cloudflare ...` | Run a bounded Cloudflare embedding batch. |
| `just embed-dual-4090-probe` | `embed probe --deployment dual-4090` | Connectivity/digest check for the Ollama pool. |
| `just embed-dual-4090-run limit="300" batch_size="8" source="claude"` | `embed run --deployment dual-4090 ...` | Run a bounded dual-GPU Ollama embedding batch. |
| `just embed-both-probe` | probes cloudflare then dual-4090 | Verify both remote deployments without opening LanceDB. |
| `just embed-both-run limit="20" batch_size="8" source="claude"` | runs cloudflare then dual-4090 | Build both vector spaces from the same bounded selection. |
| `just smoke` | `bun run smoke` | The release gate. Run before any handoff/PR. |
| `just ui` | `bun run ui` | Same as `just lesson-07`. |

Notes: `just` recipes take positional/named args with defaults (e.g.
`limit="20"`) - override with `just embed-cloudflare-run 50 16 codex`.

## 6. Every `package.json` script

| Script | Command | Purpose |
| --- | --- | --- |
| `cli` | `bun src/cli.ts` | Shorthand; still needs a subcommand appended. |
| `ui` | `bun run ui:build && bun src/server.ts` | Production build + serve. This is what you run day to day. |
| `ui:build` | `vite build` | Build the React app into `ui/dist`. |
| `ui:dev` | `vite --host 127.0.0.1 --port 4321` | Vite dev server with HMR, **separate port (4321)** from the API server (4320) - point it at a running `bun src/server.ts` for API calls during frontend dev. |
| `test` | `bun test` | Run the Bun test suite (`tests/`, `ui/src/*.test.ts`, `worker/index.test.ts`, `maw-plugin/streaming.test.ts`). |
| `typecheck` | `tsc --noEmit` | Type-check only, no emit. |
| `version:check` | `bun scripts/check-version.ts` | Assert `package.json#version` matches CalVer and matches `maw-plugin/plugin.json#version`. |
| `smoke` | `version:check && typecheck && ui:build && test && scripts/smoke.ts` | The full release gate, in that order. |
| `maw:build` | `version:check && scripts/build-maw-plugin.ts` | Stage `maw-plugin/dist/` (copies `index.ts`, writes `plugin.json` and a `project-root.txt` marker pointing back at this checkout). |
| `maw:install` | `maw:build && maw plugin install maw-plugin/dist --force` | Build then install the plugin into your local `maw` installation. |

## 7. CLI reference (every command, every flag)

Entry point: `bun src/cli.ts <command> [flags]`. Every command prints one JSON
object to stdout via `console.log(JSON.stringify(value, null, 2))`; long-running
commands (`plan`, `import`, `embed run`) also stream `[jscan] <phase> <status> ...`
progress lines to **stderr** so stdout stays pipeable to `jq`. Unknown command
falls through to `help()` then throws.

```
bun src/cli.ts choose
bun src/cli.ts init
bun src/cli.ts schema
bun src/cli.ts normalize --file <session.jsonl> [--source fixture]
bun src/cli.ts plan [--source claude|codex|fixture] [--root <directory>]
bun src/cli.ts import [--source claude|codex|fixture] [--root <directory>] [--max-files 1] [--expect-plan <revision>] [--expect-count <n>]
bun src/cli.ts embed <providers|probe|run> [--deployment m5-ollama]
bun src/cli.ts status
bun src/cli.ts events [--source claude] [--limit 20]
```

Default source when `--source` is omitted: `claude`. `--root` overrides the
preset root entirely (works with any `--source` label, including a made-up one
like `archive`).

### `choose`

No flags. Prints why LanceDB was picked (local, Arrow-native, typed tables
now + optional vectors later, no server/account) and states explicitly:
"Typed Repository/Data Mapper; not a relational ORM."

### `init`

No flags. Opens `Database.open()` and calls `db.plain.create()` - creates the
3 plain tables (idempotent; safe to call repeatedly). Reports both store
directories and their table lists. **Does not** create the vector store.

### `schema`

No flags. Prints the Arrow schema description (`schemaDescription()`) for
`events`, `event_sources`, `source_files`.

### `normalize --file <path> [--source fixture]`

Required: `--file`. Runs the normalizer against one JSONL file with **zero
database writes** (calls `preview()`, not `importSource()`). Returns block
counts, corrupt-line counts, etc. - use this to sanity-check a file before
importing it for real.

### `plan [--source ...] [--root ...]`

Read-only. Scans the root, hashes files, and returns a `PlanReport`:

```ts
{ source, root, plan_revision, found, new, changed, unchanged, shrunk, will_parse, files: FilePlan[] }
```

The CLI print strips `files` from stdout (`const { files: _files, ...summary } = report`)
to keep terminal output short; the HTTP API (`GET /api/import/plan`) returns
the full array. `plan_revision` is a deterministic fingerprint the import job
runner uses to reject a stale plan.

### `import [--source ...] [--root ...] [--max-files N] [--expect-plan <rev>] [--expect-count <n>]`

Writes. `--max-files` **bounds the write batch only** - the importer still
scans/compares the entire root first, so `remaining_files` is always accurate.
Omit `--max-files` to import everything found. `--expect-plan`/`--expect-count`
are optimistic-concurrency guards (reject if the live plan revision or parse
count has moved since you last inspected it) - the same mechanism the
background-job API uses internally.

Returns an `ImportReport` (superset of `PlanReport`):

```ts
{ ...PlanReport fields (minus files), selected_files, remaining_files, partial,
  parsed_records, blocks, inserted, duplicates, occurrences_inserted, corrupt }
```

Progress heartbeats (stderr) look like:
`[jscan] import progress 1/1 records=5 blocks=5 inserted=5 duplicates=0 corrupt=1`

Buffers commit to LanceDB every 5,000 blocks; the file manifest row is only
written after the file finishes parsing, so a killed process leaves that file
`new` again on the next run (safe, not corrupt).

### `embed <providers|probe|run> [flags]`

Subcommand dispatch (`embedAction()`): first positional arg after `embed`; if
it's missing or starts with `--`, defaults to `run`. `embed --source ...` is
therefore backward-compatible shorthand for `embed run --source ...`.

- **`embed providers`** - no flags. Lists `plugin_api_version`,
  `default_deployment` (`m5-ollama`), and `embeddingProviderRegistry.describe()`
  (every deployment plus which required env vars are present/missing). Opens
  no database, makes no network call.
- **`embed probe [--deployment m5-ollama] [--text "..."]`** - sends exactly one
  probe string through the named provider, validates the response shape/dimension,
  reports the vector norm. Opens no LanceDB. Use before a real run to confirm
  connectivity and that the model/revision matches what the deployment expects.
- **`embed run [flags]`** - the real batch:
  - `--deployment m5-ollama|dual-4090|cloudflare` (default `m5-ollama`)
  - `--source claude|codex|fixture` (or any custom source label already imported)
  - `--project <name>` / `--oracle <name>` (aliases; either works, matches the normalized `project` field)
  - `--folder <directory>` (matches files **directly inside** one provenance folder; not recursive into nested folders)
  - `--since YYYY-MM-DD` / `--until YYYY-MM-DD` (inclusive, `Asia/Bangkok` calendar days)
  - `--limit 300` (default `DEFAULT_EMBED_LIMIT = 300`; how many events to embed this run)
  - `--batch-size 8` (default `DEFAULT_EMBED_BATCH_SIZE = 8`; texts per provider HTTP call)
  - `--retries 2` (default 2; exponential backoff, 500ms base delay, doubling each attempt)

  Credentials are **never** accepted as CLI values - only from environment
  variables (enforced by design, not just convention).

### `status`

No flags. Full inventory: both store directories + table lists, vector store
health (`healthy` / `missing` / `error`, with error message if opening it
threw), row counts per table, embedding config constants (model/dimension/text
policy), and a per-source breakdown of `events` / `event_sources` / `source_files`
counts.

### `events [--source ...] [--limit 20]`

Read the `events` table directly (not through the paginated UI facet path).
`--limit` is clamped to `min(limit, 200)`. Optional `--source` filters with a
SQL `WHERE source = '...'` (values are escaped via the `sql()` helper).
Returns `id, timestamp, project, semantic_role, block_type, source, text`.

### `help` / `--help` / `-h` (also the default for any unrecognized command)

Prints the full command summary shown above, then (for a truly unknown
command) still throws `unknown command: <name>` so scripts fail loudly.

## 8. HTTP API reference (what the UI actually calls)

`src/server.ts` is a single `Bun.serve()` handler bound to `127.0.0.1` only
(hostname is hardcoded; `validateLocalHost()` also rejects any request whose
`Host` header isn't `127.0.0.1`/`localhost`/`[::1]`/`::1` with a 400, even if
you did get a socket connection some other way). Idle timeout 255s. Useful if
you want to script against the running UI instead of the CLI, e.g. from a
browser extension, curl, or your own dashboard.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/`, `/admin`, `/admin/` | Serves the built `ui/dist/index.html`; 503 with a JSON error if you haven't run `ui:build`. |
| GET | `/api/status` | Same shape as CLI `status`, plus `fixture_root` and `source_presets`. |
| GET | `/api/events?source=&project=&folder=&limit=` | Paginated event browser with facets; `limit` clamped 1-200. |
| GET | `/api/events/facets?source=&project=` | Just the project/folder facet counts. |
| GET | `/api/events/live?source=&project=&limit=` | Bounded tail window, **no facet computation** - the "fast lane" used while a job is actively writing. |
| GET | `/api/history?period=day\|week\|month&date=YYYY-MM-DD&source=&project=&folder=` | Calendar reconstruction; responses cached 45s server-side (cache is bypassed/invalidated while a job is running). |
| GET | `/api/history/session?date=&source=&project=&folder=&session_id=&offset=&limit=` | Full chronological session detail, paginated. All params but `offset`/`limit` are required. |
| GET | `/api/vectors/visualize?deployment=dual-4090\|cloudflare&date=&source=&project=&folder=&session_id=&limit=&actor=human,agent` | 2D/3D projection for the History vector inspector. `deployment` is restricted to `dual-4090` or `cloudflare` here - **`m5-ollama` is not a valid value for this endpoint** (see Limits, #6). |
| GET | `/api/import/plan?root=&source=&plan_state=&compare=` | Exact plan (hashes files). `plan_state`: `all`\|`actionable`\|`new`\|`changed`\|`unchanged`\|`shrunk`. `compare`: `full`\|`metadata`. |
| GET | `/api/import/intake?root=&source=` | Cheap metadata-only scan (no hashing, no DB writes) - what the UI polls every 30s. Returns `found/new/changed/indexed/reconcile/actionable`. |
| POST | `/api/import` | Body `{root, source, maxFiles: 1-100}`. Synchronous bounded import; requires `content-type: application/json` and a same-origin (or absent) `Origin` header. |
| POST | `/api/jobs/import` | Body `{mode: "batch"\|"all", root, source, expectedPlanRevision, expectedWillParse, planPolicy?: "exact"\|"refresh", maxFiles? (batch only, 1-100)}`. Starts a background job; 409 if a writer is already active. Returns 202. |
| GET | `/api/jobs` | `{jobs: [...], active_id}`. |
| GET | `/api/jobs/:id/log?from=0` | Incremental log tail by cursor. |
| POST | `/api/jobs/:id/cancel` | Only valid while `running` or `cancelling`; 409 otherwise. |
| GET | `/assets/*` | Built UI static assets, cached `immutable` for a year. |

Request-body cap: 16 KiB (`MAX_BODY_BYTES`), checked against both the
`content-length` header and the actual decoded byte length. Every mutating
POST validates `content-type: application/json` and rejects a cross-origin
`Origin`. Job history is **in-memory and bounded** - it does not survive a
server restart (this is by design, per lessons/07, not a bug).

## 9. Every env var / config knob

Grepped from every `process.env.*` reference in `src/`, `scripts/`, and
`maw-plugin/` (test files excluded):

| Variable | Read in | Default if unset | What it controls |
| --- | --- | --- | --- |
| `PLAIN_DB_DIR` | `database.ts`, `cli.ts`, `server.ts` | - | Explicit override for the plain store directory. Checked before `DB_DIR`. |
| `DB_DIR` | `database.ts`, `cli.ts`, `server.ts`, `scripts/smoke.ts` | `<repo>/.data/lancedb` | **Legacy/compat alias** for the plain store directory - still fully supported. |
| `VECTOR_DB_DIR` | `database.ts`, `cli.ts`, `server.ts` | `<plain dir>.vector` (or `.vector.<space-id>` for a non-default space) | Explicit override for the vector store directory. |
| `DUAL_4090_VECTOR_DB_DIR` | `server.ts` | falls back to `VECTOR_DB_DIR` | History-vector-inspector-only override for where the dual-4090 space is read from. |
| `CLOUDFLARE_VECTOR_DB_DIR` | `server.ts` | derived default vector dir for the Cloudflare space | Same, for the Cloudflare space. |
| `PORT` | `server.ts`, `maw-plugin/index.ts` | `4320` | HTTP server port. |
| `M5_OLLAMA_URL` | `embedding-provider.ts` | `http://127.0.0.1:11434` | Base URL for the `m5-ollama` deployment. |
| `OLLAMA_URL` | `embedding-provider.ts` | - | Secondary fallback if `M5_OLLAMA_URL` is unset (checked after it). |
| `DUAL_4090_OLLAMA_URLS` | `embedding-provider.ts` | - (**required**, throws if empty) | Comma-separated Ollama endpoint URLs for the `dual-4090` pool (round-robin + failover, sharded across endpoints for multi-text batches). |
| `CLOUDFLARE_ACCOUNT_ID` | `embedding-providers/cloudflare.ts` | - (required for `cloudflare` deployment) | Cloudflare account ID. Never printed by provider inspection. |
| `CLOUDFLARE_API_TOKEN` | `embedding-providers/cloudflare.ts` | - (required) | Bearer token for Workers AI. Never printed, never accepted as a CLI flag. |
| `CLOUDFLARE_AI_BASE_URL` | `embedding-providers/cloudflare.ts` | Cloudflare's default API base | Override the Workers AI REST base URL. |
| `JSCAN_PROGRESS_INTERVAL_MS` | `cli.ts` | `1000` | Throttle interval (ms) for stderr heartbeat lines during long `plan`/`import`/`embed run` calls. Lower it (e.g. `5`) in tests/CI to see heartbeats fire fast. |

Also present as a config file: `.env.example` documents the four
deployment-relevant vars (`M5_OLLAMA_URL`, `DUAL_4090_OLLAMA_URLS`,
`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`) - copy it to `.env` and Bun
will auto-load it (Bun reads `.env` natively; no `dotenv` dependency in
`package.json`). `.env*` is git-ignored.

Note: `assertSeparateDirectories()` in `database.ts` throws at open time if
the plain and vector directories resolve (after symlink/realpath resolution)
to the same physical path - so you cannot accidentally point both at one dir.

## 10. UI screens, workspace by workspace

`bun run ui` then open `http://127.0.0.1:4320`. Three top-level workspaces
live in one command bar with no page reload between them: **Events**,
**History**, **Jobs**. (The "Vector map" is not a fourth top-level tab - it's
an inspector opened per-session from inside History; see below. The README's
bullet list groups it as a peer for narrative purposes, but the actual route
model in `ui/src/location.ts` is `WorkspaceName = "events" | "history" | "jobs"`.)
Workspace, active job, source, project, folder, view, history period/date, and
vector-inspector state are all encoded in the URL - reload-safe, back/forward-safe,
shareable link.

Two themes: **Dark** (default) and **Paper**, switchable, structurally
identical - a theme change only swaps color tokens, never layout or content.
Interface font is IBM Plex Mono (monospace throughout - labels, counts, paths,
timestamps); headings use IBM Plex Sans Variable.

### Events workspace

The default landing view. A control rail (left, desktop) holds: source
picker (Claude Code / Codex / Fixture presets, or a custom root), stored-row
totals, the equivalent CLI command for whatever you're about to do, the last
import report, and a live-intake reading that polls `/api/import/intake`
every 30 seconds - shows New / Changed / Indexed / Reconcile counts without
touching the imported event workspace, pauses while the tab is hidden or a
writer is active.

Main pane has two modes over the same filtered window:

- **Stream** (default) - dense grid of canonical event rows: time,
  source/block type, project/semantic role/folder, and the canonical text
  (long blocks clamp and expand in place).
- **Visualize** - five summary charts over the *same currently-filtered
  window* (never a separate analytics query): activity pulse (12
  chronological buckets), block-type distribution, semantic-role
  distribution, project distribution, folder distribution.

Filters (Source, Project/Oracle, Directory/Folder) are server-backed query
scope, not client-side decoration - options come from real facet counts.
`Cmd+K` / `Ctrl+K` focuses a searchable Project/Oracle combobox anywhere in
the app. Changing Source clears the dependent Project/Folder selections.

**Import Plan modal**: opened from "Inspect plan." Read-only, centered dialog,
4 fixed regions (header/filter-toolbar/file-body/pager) with only the file
body scrolling. Shows 40 files per page, filterable by path substring and by
state (all/actionable/new/changed/unchanged/shrunk). Batch size is chosen in
the plan footer; clicking "Start import" swaps that footer in place for an
explicit confirmation step (repeats the exact batch size and root, states
plainly that source JSONL is untouched) - **the two-step confirm is
deliberate**, not an extra click to remove.

### Jobs workspace

Every interactive import automatically switches here. Each job row shows
lifecycle state (`running`/`cancelling`/`succeeded`/`failed`/`cancelled`),
timestamps, exit code, and the live `[jscan]` stderr/stdout stream from the
real CLI child process - "the browser does not invent progress; it shows the
same fixed-argument CLI process ... as maw." Running jobs expose Cancel and
Copy-log. A successful job links straight to its imported events; a
failed/cancelled one links back to a fresh plan review (because a cancelled
run may still have committed idempotent partial batches - always re-plan
after a cancel, don't assume zero was written). Job history is in-memory,
newest-first, and bounded - it resets on server restart.

### History workspace

A full-width forensic ledger over already-imported canonical events (never
inferred from filesystem mtimes). Three periods - **Day / Week / Month** - all
computed in `Asia/Bangkok` time; weeks run Monday-Sunday; every calendar date
in range renders even with zero events ("absence is a finding, not a gap to
remove"). Each row: date + observed time range, a compact numeric `Src #`
badge (stable across the whole DB catalogue, not just the current window),
project/folder, session ID, daily event count, a one-line evidence preview,
and continuation markers showing whether the session continues into the
previous/next day. `View contents` expands a session's full chronological
canonical blocks in place, paginated.

**Vector inspector** - opened per session row without leaving History. Select
the local `dual-4090` index, the managed `cloudflare` index, or both side by
side (never overlaid - different embedding spaces are never mixed on one
plot). Human/Agent tick filters apply before sampling/projection. Two
pluggable visualizers: **Atlas 3D** (Three.js, lazy-loaded, optional
motion-aware spin) and **Flat 2D** (SVG, the stable fallback - Atlas 3D falls
back to Flat 2D on plugin failure, never silently to a different embedding
provider). Selection is coordinated across panels by `event_id`, never by
plot coordinates. Before any embedding run, this panel is still useful: it
identifies the requested deployment/model/dimensions and reports the specific
missing-store reason instead of erroring the whole workspace out.

### Cloudflare static fixture demo

The public link (`https://lanceglass-fixture-demo.laris.workers.dev/`) is the
*exact same production React build*, deployed as a Cloudflare Worker
(`worker/index.ts`, `wrangler.toml`) with 1,000 bundled synthetic events and a
complete mock HTTP API. No KV/D1/R2/database binding, no filesystem, no
secrets, no persistence - every "write" (import, job start) is a deterministic
simulation that resets on reload. Safe to poke at before ever running the
real thing locally.

## 11. Configuration: default roots, default data dirs, how to point elsewhere

Source presets (`src/sources.ts`, `SOURCE_PRESETS`):

| `--source` id | Label | Default root |
| --- | --- | --- |
| `claude` (default) | Claude Code | `~/.claude/projects` |
| `codex` | Codex | `~/.codex/sessions` |
| `fixture` | Bundled fixture | `<repo>/fixtures/minimal` |

Pass `--root <dir>` (CLI) or `?root=<dir>` (API/UI) to use any directory with
any source label - presets are just convenient defaults, not a closed set
(`resolveSourceSpec()` falls back to a custom root+label pair whenever `root`
is non-empty; only an *unknown preset id with no root* is rejected).

Data directories: plain store defaults to `<repo>/.data/lancedb`, vector
store to `<plain>.vector` (see the env var table in section 9 for every
override). Both are git-ignored. **Never point the UI/importer at a private
archive until the fixture-only `bun run smoke` passes clean from a fresh
database** (this is stated explicitly in `lessons/07-ui.md` as a gate, not a
suggestion).

## 12. Optional embeddings, in depth

Two-store separation exists specifically so that import stays "a fast,
inspectable fact-gathering operation" that never depends on a model server
being up. Embedding is explicitly derived data, rebuildable at any time from
the plain store.

Order of operations for a first embedding run:

```bash
# 1) Make sure you have plain rows to embed
bun src/cli.ts import --source claude --max-files 1
bun src/cli.ts events --source claude --limit 20

# 2) Check deployment readiness (no network calls that touch LanceDB)
bun src/cli.ts embed providers
bun src/cli.ts embed probe --deployment m5-ollama

# 3) Run a bounded, resumable batch
bun src/cli.ts embed run --deployment m5-ollama --source claude --limit 300 --batch-size 8
```

Built-in deployments (`src/embedding-provider.ts`, `EMBEDDING_DEPLOYMENTS`):

| Deployment id | Transport | Vector store sharing |
| --- | --- | --- |
| `m5-ollama` | one local Ollama endpoint (`M5_OLLAMA_URL`) | Shares the pinned Ollama BGE-M3 store (`ACTIVE_EMBEDDING_SPACE`). |
| `dual-4090` | round-robin/failover Ollama pool (`DUAL_4090_OLLAMA_URLS`) | Shares the **same** store as `m5-ollama` - verified byte-identical model digest across both. |
| `cloudflare` | Cloudflare Workers AI native REST (`CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN`) | **Isolated** store - Workers AI exposes no public model digest, so the adapter sends one deterministic revision-probe string, hashes the returned Float32 bytes, and refuses on fingerprint mismatch. |

Model/contract constants: `bge-m3`, 1024-dim `Float32`, cosine distance, input
text is `event.text.slice(0, 2000)` (`EMBEDDING_TEXT_LIMIT = 2000`). Only
events with `semantic_role` in `human_intent`/`summary`/`assistant_answer`
(never raw `tool_action`/`tool_evidence`) and post-truncation text longer than
80 characters are eligible (`isEmbeddableEvent()` also excludes
`<system-reminder>` and `[Image: source:` prefixed text).

Scoping flags for `embed run`: `--project`/`--oracle` (exact normalized-project
match), `--folder` (direct children of one provenance folder only, not
recursive), `--since`/`--until` (inclusive Bangkok-calendar dates).

**Resume correctness**: each vector row carries `event_id, source, project,
session_id, timestamp, text_hash, model, dimension, embedded_at, vector`. A
later `embed run` pages plain-store candidates, looks up only the matching
vector IDs, and skips anything whose `text_hash`/`model`/`dimension`/copied
scope metadata already match - so a failed batch is safe to just rerun.
Completed batches are durable before the next provider call. A file lock
(`<vector-dir>.event_vectors.lock`, hard-link-based, PID-stamped) prevents two
`embed run` processes from writing the same vector store concurrently -
you'll get a clear "writer is already active (pid N)" error, not silent
corruption.

**Do not delete the plain store to rebuild vectors.** Delete only the vector
store when you deliberately change the embedding contract:

```bash
rm -rf .data/lancedb.vector
```

## 13. Optional `maw` adapter

If [`maw`](https://github.com/Soul-Brews-Studio/maw-js) is installed:

```bash
bun run maw:install         # builds maw-plugin/dist and installs it
maw jscan plan --source claude
maw jscan import --source claude --max-files 10
maw jscan ui --port 4320
maw jscan embed providers
maw jscan embed probe --deployment m5-ollama
maw jscan embed run --deployment dual-4090 --source claude --limit 100
maw jscan status
maw jscan events --source claude --limit 20
```

The adapter (`maw-plugin/index.ts`) is a thin process wrapper: it locates the
real project root (via a `project-root.txt` marker written at build time),
`Bun.spawn`s the exact same `bun src/cli.ts ...` (or `bun src/server.ts` for
`ui`), forwards stdout/stderr line-by-line, and relays `SIGINT`/`SIGTERM`/abort
signals to the child. It duplicates **zero** importer logic - this is the same
"one engine everywhere" claim the README makes for CLI vs UI vs maw.

Caveat carried over verbatim from `lessons/06-cli.md`: the current maw
dev-plugin host buffers both stdout and stderr until process exit whenever
stderr has no TTY (CI, redirected output, etc.) - so you will not see live
heartbeats in that situation; you'll get everything at once at completion.
True streaming there needs a future maw host streaming mode.

The build marker itself (`maw-plugin/dist/project-root.txt`) is intentionally
untracked/unpublished - it's a local checkout pointer, not source history.

## 14. Teardown / reset paths

Reset **everything** (plain + vector):

```bash
rm -rf .data/lancedb .data/lancedb.vector
```

Reset **only the plain store** (forces a full reimport on next run, tables
recreate automatically and idempotently):

```bash
rm -rf .data/lancedb
```

Reset **only the vector store** (correct move when you change embedding
contract/model - never nuke the plain store just to rebuild vectors):

```bash
rm -rf .data/lancedb.vector
```

Stop the server: `Ctrl+C` (SIGINT) or SIGTERM - `server.ts` has a graceful
`shutdown()` that stops accepting connections, shuts the job manager down
(so an in-flight background import isn't just abandoned), then exits 0.
Safe to Ctrl+C mid-import: stable IDs make the next run idempotent, and a
file's manifest row is only written after that file finishes parsing.

`bun run smoke` never touches your real `.data/` - it works entirely inside
a fresh `mkdtemp()` temp directory that's `rm -rf`'d in a `finally` block even
on failure.

## 15. Known limits, caveats, and things that do not work

1. **No live-streamed progress under a non-TTY stderr host** (see section 13)
   - maw's current dev-plugin host buffers to end-of-process there. A future
   maw streaming mode is required, not something Lanceglass alone can fix.
2. **Job history does not persist.** It's in-memory and bounded by design
   (`lessons/07-ui.md`); a server restart loses the Jobs list, though it does
   not lose or corrupt any already-imported LanceDB rows.
3. **`m5-ollama` is not selectable in the History vector inspector.**
   `HISTORY_VECTOR_DEPLOYMENTS = ["dual-4090", "cloudflare"]` in
   `src/history-vectors.ts` - only those two IDs are valid for
   `/api/vectors/visualize`, even though `m5-ollama` is a perfectly valid
   `embed run --deployment` target. If you only ever embed with `m5-ollama`,
   you will not see it in the vector map (it shares the same physical store
   as `dual-4090` though, so embedding via `m5-ollama` and then viewing under
   `dual-4090` in the inspector does work, since they're the same vector space).
4. **No public model digest for Cloudflare Workers AI.** The adapter
   substitutes a self-computed deterministic probe fingerprint instead of a
   real digest comparison - documented as a deliberate workaround, not a full
   guarantee, since Workers AI "can produce tiny batch-shape-dependent
   floating-point differences for the same text" (the probe call is
   single-text specifically to sidestep that).
5. **No dedicated browser/E2E UI test suite.** `lessons/07-ui.md`: "Focused
   backend tests are included; there is no dedicated browser-test suite" -
   coverage is backend/API-level plus `ui/src/*.test.ts` unit tests for pure
   logic (history-date, history-sort, plan-filter, vector-visualizations,
   etc.), not full-browser interaction tests.
6. **This is explicitly not a production multi-user service.** Loopback-only
   binding, no auth beyond Host/Origin checks, 16 KiB request cap, no
   telemetry - it is developer tooling for one person's local machine
   (`SECURITY.md`: "This is local developer software, not a hardened
   multi-user hosted service").
7. **Not a relational ORM.** No joins, foreign keys, or transactions -
   relationships/invariants live in the TypeScript repository layer
   (`src/database.plain.ts` etc.), not in LanceDB itself. This is a stated
   design trade-off (`lessons/01-choose-db.md`), not a missing feature.
8. **`--folder` for `embed run` is not recursive.** It matches only files
   directly inside the named provenance folder; nested subfolders need their
   own `--folder` run or a broader unscoped run.
9. **Public-safety discipline is manual, not automated for forks.**
   `SECURITY.md` gives grep commands to run against full commit history
   before publishing a fork - there's no pre-push hook enforcing it in this
   checkout.

## 16. Lessons 01-08, summarized

The `lessons/` directory is the repo's own "smoke-first learning path" - eight
short files, each pairing one architectural decision with the exact `just`/`bun`
command that proves it. Below: each lesson's core claim plus the evidence the
lesson itself points at.

### Lesson 01 - Choose the database

**Claim:** LanceDB is the right fit *because* it's local, embedded, Arrow-native,
needs no server/account, supports plain typed tables today and a vector table
later without switching databases - and it is explicitly **not** a relational
ORM, so relationships/invariants belong in a small Repository/Data Mapper
boundary instead of SQL constraints.
**Evidence:** Decision checklist in the lesson (local+disposable, explicit
Arrow schemas, TS/Bun support, no server, vector-search-later) is directly
satisfiable by reading `package.json`'s `@lancedb/lancedb` + `apache-arrow`
dependencies. Verification command: `just smoke`.

### Lesson 02 - Create the database

**Claim:** The plain database lives at a lab-local, fixed path
(`.data/lancedb`) that must never fall back to another lab's data directory,
and table creation must be idempotent - running init/smoke twice must not
error just because the tables already exist.
**Evidence:** `rm -rf .data/lancedb && just smoke` then `just smoke` again -
the second run must succeed without a "table exists" failure. This is exactly
what `scripts/smoke.ts` phase 2 (`cli("init")`, asserting `tables.length === 3`)
and `PlainDatabase.open()`'s idempotent-create logic implement.

### Lesson 03 - Typed ORM-like repository

**Claim:** Database access is "ORM-like, not a full ORM" - three separate
layers (domain row TypeScript types, runtime Arrow schemas, and Repository
classes) so the importer, CLI, and UI never scatter raw table names or filter
strings throughout the codebase. The repository boundary should make five
operations obvious: init/open tables, find a source file by identity, insert
a canonical event only if new, record provenance, and list/count for reads.
**Evidence:** Read order the lesson prescribes - row types -> Arrow schemas ->
`.data/lancedb`-rooted connection -> repositories used by import/CLI/UI.
Verified by `just smoke` succeeding without any test framework, i.e. the
CLI alone can create and read the database through typed methods.

### Lesson 04 - Normalize JSONL

**Claim:** Normalization is the boundary between messy source records and
stable stored rows - it must parse line by line, keep meaningful
user/assistant/tool/summary content, skip irrelevant telemetry, and report
malformed lines *without* discarding the rest of the file. Critically: the
same input must always normalize to the same identity (deterministic), or
Lesson 05's new-vs-known distinction breaks.
**Evidence:** `just smoke`'s normalization phase against the bundled fixture
- small enough that every kept/skipped row is individually inspectable. In
practice this is `scripts/smoke.ts` phase 4: `normalize --file session.jsonl`
asserts exactly `blocks === 5` and `corrupt === 1` from the fixture, every
single time.

### Lesson 05 - Import: new vs known

**Claim:** Two independent identity concepts are required: **source file
identity** (is this file new or known) and **canonical event identity** (is
this normalized block new or known, globally) - kept separate so the same
canonical event can be observed again from a different file without
duplicating it. Also documents the fast/cheap intake scan (metadata-only,
polled every 30s by the UI) versus the exact/expensive plan (hashes content,
returns a `plan_revision` background jobs use to reject staleness), and the
exactly-once-flush guarantee: import snapshots the byte length observed at
preflight and only hashes/parses that immutable prefix, so bytes appended to
a live JSONL mid-import are picked up as a "changed" file on the *next*
idempotent pass, not corrupted into the current one.
**Evidence:** `rm -rf .data/lancedb && just smoke` walks the exact 4-step
cycle: plan reports 2 new -> `--max-files 1` selects one, 1 remaining ->
resume imports the second, 0 remaining -> repeat reports both known, zero new
canonical rows. This is `scripts/smoke.ts` phases 5-8 verbatim, down to the
literal count assertions (`remaining_files` 1 -> 0, final `events === 7`).

### Lesson 06 - CLI

**Claim:** The CLI's job is to expose the same repository the importer uses,
without requiring anyone to poke at LanceDB internals - init/inspect,
normalize/import, new-vs-known, status/counts/recent-events, and (where
implemented) search/filter. Progress is a **separate stream** from data:
interactive terminals get live phase/heartbeat lines on stderr while the one
final machine-readable report stays on stdout, specifically so a long LanceDB
merge doesn't look frozen without corrupting anything piped to `jq`.
Also: `--max-files` bounds the **write** batch, not the discovery/scan pass.
**Evidence:** `just smoke`'s CLI phase, plus the explicit caveat that the
current maw dev-plugin host buffers both streams to end-of-process when
stderr has no TTY (documented as a known gap, needing a future maw streaming
host mode - not fixable from this side).

### Lesson 07 - UI

**Claim:** The UI is "another interface to the same importer - not a browser
side reimplementation." Its Bun API plans through the shared importer and
starts the real CLI as a guarded background job; React only displays state
(source-file state, live stdout/stderr, partial progress, stored counts,
canonical events). The bounded-import button is deliberately two-step (fresh
GET plan first, "Start import" second) so the operator always sees the exact
new/changed count and root before any write. A terminal job triggers exactly
one authoritative full refresh, while live progress reads only bounded
job-log/event-window state - it never repeats the heavyweight full status/facet
query path while LanceDB is actively writing.
**Evidence:** `just smoke`'s UI portion (phases 2 and 7-9 of `scripts/smoke.ts`):
starts the server in a one-file-imported state, verifies the plan endpoint
reports one remaining file, resumes safely, starts a revision-guarded job via
`POST /api/jobs/import`, polls `/api/jobs`, reads its incremental log, loads
the production React document plus one bundled asset, stops the server
cleanly. Explicitly notes: "there is no dedicated browser-test suite" - only
focused backend tests plus pure-logic unit tests cover the UI layer.

### Lesson 08 - Optional embeddings, after plain import

**Claim:** Two physical LanceDB stores exist *on purpose* - `database.plain`
(`.data/lancedb`: events/event_sources/source_files, touched by every
plan/import/UI read) and `database.vector` (`.data/lancedb.vector[.<space-id>]`:
event_vectors only, touched only by an explicit embedding or future
semantic-search call). Import must stay "a fast, inspectable fact-gathering
operation" that completes and stays resumable even if a model server is slow,
down, or returns garbage - so it never calls an embedding endpoint. Embedding
is treated as derived data, rebuildable at any time from the plain store.
Resume correctness is achieved by copying scope metadata (`source, project,
session_id, timestamp`) plus a `text_hash` of the *exact* truncated input into
each vector row, so a rerun can skip anything already current and safely
continue anything left stale after a failed call.
**Evidence:** The lesson's own code sketch -
`importSource(database.plain, spec)` takes no provider argument at all;
`embedPending(database.plain, database.vector, provider, {...})` is a
separate, explicit call. Command sequence: `embed providers` -> `embed probe`
-> `embed run` (both an unscoped run and a `--oracle`/`--since`/`--until`-scoped
partial pass, plus a `--folder`-scoped run against exact JSONL provenance).
Explicit warning embedded in the lesson: do not delete the plain store to
rebuild vectors - delete only `.data/lancedb.vector`, and only when the
embedding contract itself changes (the new scope-metadata schema described
here is itself cited as one such breaking change requiring exactly that
reset).

## 17. Project map

```text
src/          typed schemas, repositories, normalization, import, history, vectors, CLI, server
ui/           React application and visualization plugins (Vite + Tailwind 4)
tests/        backend and integration tests (bun test)
fixtures/     synthetic JSONL only (session.jsonl: 6 lines/5 blocks + 1 corrupt; z-session.jsonl: 2 lines)
lessons/      the smoke-first learning path summarized above
docs/         architecture diagram, UI state gallery, embedding + vector-viz extension contracts
maw-plugin/   optional local CLI adapter (source of truth: index.ts; dist/ is generated, untracked)
worker/       Cloudflare Worker for the public static fixture demo (wrangler.toml)
scripts/      smoke.ts (release gate), check-version.ts, build-maw-plugin.ts
```

Extension points, if you're building on this rather than just running it:
- New embedding provider: `docs/embedding-provider-plugins.md` (source
  plugins only, statically imported - the registry never downloads/executes
  a remote package; add to `src/embedding-providers/` +
  `BUILTIN_EMBEDDING_PROVIDER_PLUGINS` in `src/embedding-plugins.ts`).
- New vector visualizer: `docs/vector-visualization-plugins.md` (implement
  `VectorVisualizationProps`, register in `ui/src/vector-visualizations.ts`;
  built-ins are `3d` = Atlas 3D / Three.js and `2d` = Flat 2D / SVG).

---

### Note on verification

Every command, flag, default, and constant above was confirmed by reading the
actual source (not the docs alone) - `src/cli.ts` for CLI parsing,
`src/server.ts` for routes, `scripts/smoke.ts` for exact expected values,
`src/schemas.ts`/`src/embedding-provider.ts`/`src/embeddings.ts` for
constants. I did not run `bun install` or `bun run smoke` against this
checkout myself, to avoid writing `node_modules`/build output into the source
repo per this task's instructions. Given `scripts/smoke.ts` hardcodes its own
literal expected outputs (e.g. `blocks === 5`, `events === 7`) as assertions
rather than descriptions, the confidence here is high without independent
execution - but if you want a live "yes it still passes" check, `bun run smoke`
is a single self-contained command that takes well under a minute and cleans
up entirely after itself in `/tmp`.
