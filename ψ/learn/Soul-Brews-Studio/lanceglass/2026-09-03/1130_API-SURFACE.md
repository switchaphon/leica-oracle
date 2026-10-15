# lanceglass - Public Surface & Extension Points

Source read from `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/`
(repo `Soul-Brews-Studio/lanceglass`, `package.json#version` = `26.9.1-alpha.1401`).
Runtime: Bun 1.3. All line numbers below are exact at this checkout.

**TL;DR for integration**

- Real HTTP API lives in `src/server.ts` (Bun.serve, **loopback-only**, real LanceDB). A second,
  API-shape-compatible server (`worker/index.ts`) exists only as a **static, in-memory Cloudflare
  Worker demo** - no persistence, not the product.
- There is **no MCP server, no `tools/list`/`tools/call`, no JSON-RPC surface anywhere in this
  repo.** Confirmed by a repo-wide case-insensitive grep for `mcp` (zero hits outside this
  report) and for `tools/list`/`tools/call` (zero hits). See §2.
- `maw-plugin/` is not a protocol server either - it's a ~180-line process adapter that forwards
  argv into `bun src/cli.ts` and streams stdout/stderr. See §3.
- `skills-lock.json` is unrelated to lanceglass's own runtime - it's an external Claude-Skills
  lockfile with zero consumers inside this repo. See §4.
- The two real, statically-typed extension points are the **embedding provider plugin**
  (`src/embedding-plugin.ts`) and the **vector visualization plugin**
  (`ui/src/vector-visualization.ts`) - both compile-time TypeScript registries, never
  runtime-loaded. See §5.
- Concrete integration recipes (HTTP / CLI / maw / "build your own MCP shim") are in §8.

---

## 1. HTTP endpoints

Two servers answer overlapping paths. **Only `src/server.ts` talks to real LanceDB.**
`worker/index.ts` is a synthetic demo deployed as the `lanceglass-fixture-demo` Cloudflare
Worker (see §7) - its handlers regenerate 1,000 fake events in memory at module load and never
touch a filesystem, KV, or D1. Differences are called out per-row.

All responses are JSON, `cache-control: no-store` (`src/server.ts:123-132`; demo variant adds
`x-lanceglass-demo: static-fixture`, `worker/index.ts:76-79`). Real-server errors are
`{ "error": "<message>", ...details? }` with status chosen by exception type
(`src/server.ts:856-863`): `HttpError.status` as thrown, `HistoryInputError`->400,
`HistoryVectorInputError`->400, `HistoryVectorStoreError`->422, anything else->500 (with `db_dir`
attached for diagnostics).

**Every request** (not just mutations) is rejected with `400 {"error":"requests require a local
Host"}` unless the `Host` header resolves to `127.0.0.1`, `localhost`, `[::1]`, or `::1`
(`validateLocalHost`, `src/server.ts:641-646`) - verified live below. There is no CORS header
anywhere in `src/server.ts`, and mutating requests additionally require
`content-type: application/json` and (if an `Origin` header is present at all) that it equal the
request's own origin (`validateMutation`, `src/server.ts:648-653`). There is **no authentication**
of any kind - this is a deliberate local-first, single-user design, not a hardened multi-tenant
API (see `PRODUCT.md`, README "Privacy boundary").

| Method | Path | Real server (`src/server.ts`) | Demo worker (`worker/index.ts`) |
|---|---|---|---|
| GET | `/health` | **absent** | `worker/index.ts:214` |
| GET | `/`, `/admin`, `/admin/` | serves `ui/dist/index.html` (`:745-754`) | falls through to `env.ASSETS` |
| GET | `/api/status` | `:755-757` -> `getStatus()` `:163-202` | `:215-223` |
| GET | `/api/events` | `:758-767` -> `getEvents()` `:204-214` | `:224-228` |
| GET | `/api/events/facets` | `:768-772` -> `getEventFacets()` `:216-222` | `:229` |
| GET | `/api/events/live` | `:773-781` -> `getLiveEvents()` `:224-238` | `:224-228` (same handler as `/api/events`) |
| GET | `/api/history` | `:782-784` -> `getHistory()` `:516-544` | `:232` |
| GET | `/api/history/session` | `:785-787` -> `getHistorySession()` `:553-592` | `:233` |
| GET | `/api/vectors/visualize` | `:788-790` -> `getHistoryVectorVisualization()` `:594-603` | `:234` |
| GET | `/api/import/plan` | `:791-799` -> `importer.plan()` | `:231` |
| GET | `/api/import/intake` | `:800-803` -> `importer.intake()` | `:230` |
| POST | `/api/import` | `:804-814`, exclusive writer lock, synchronous | `:238`, always returns canned demo report |
| POST | `/api/jobs/import` | `:815-818`, async job, `202` | `:237`, always `202` with fixed demo id |
| GET | `/api/jobs` | `:819-821` | `:235` |
| GET | `/api/jobs/:id/log` | `:822-830` | `:236` |
| POST | `/api/jobs/:id/cancel` | `:831-842`, real cancel | `:239`, **always `409`** ("Static demo jobs are immutable.") |
| GET | `/assets/*` | `:843-854`, immutable 1y cache | n/a (served by `env.ASSETS`) |
| * | anything else under `/api/` | `404 {"error":"not found"}` (`:855`) | `:240` |

Notable asymmetry: the demo's `/api/events` response embeds `facets` inline
(`worker/index.ts:227`, `...body, facets: facets(url)`); the **real** server's `/api/events`
always returns an empty `facets: {projects:[],folders:[]}` stub and requires a *separate* call to
`/api/events/facets` (`event-browser.ts:64-66`, deliberately - the comment there says facets are
split out "so the first visible rows are never held behind multi-million-row project/folder
aggregation"). An integration written against the public demo will see a shape the real server
does not produce on that endpoint.

### 1.1 Per-endpoint detail

JSON below marked **"live"** was captured by importing the repo's own bundled fixture
(`fixtures/minimal/`) into an isolated temp LanceDB directory and hitting a real
`bun src/server.ts` instance on loopback - nothing here touched real agent history. JSON marked
**"shape"** is built directly from the cited type/validation code, not captured live (covers
branches the fixture can't easily reach, e.g. a populated vector store or a running job).

#### `GET /api/status` - live
No query params. Handler: `src/server.ts:163-202`.
```json
{
  "db_dir": "/tmp/.../plain",
  "vector_db_dir": "/tmp/.../vector",
  "databases": {
    "plain": { "directory": "/tmp/.../plain", "tables": ["event_sources", "events", "source_files"] },
    "vector": { "directory": "/tmp/.../vector", "present": false, "health": "missing", "error": null, "tables": [], "event_vectors": 0 }
  },
  "fixture_root": "/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/fixtures/minimal",
  "source_presets": [
    { "id": "claude", "label": "Claude Code", "root": "/Users/switchaphon/.claude/projects", "default": true },
    { "id": "codex", "label": "Codex", "root": "/Users/switchaphon/.codex/sessions" },
    { "id": "fixture", "label": "Bundled fixture", "root": ".../fixtures/minimal" }
  ],
  "tables": { "events": 7, "event_sources": 7, "source_files": 2 },
  "sources": { "fixture": { "events": 7, "event_sources": 7, "source_files": 2 } }
}
```
`vector.health` is `"missing"` | `"healthy"` | `"error"` (`optionalVectorStatus`, `:134-161`).
`source_presets` is the literal `SOURCE_PRESETS` array from `src/sources.ts:13-30` - `claude`
(`~/.claude/projects`, default), `codex` (`~/.codex/sessions`), `fixture` (bundled).

#### `GET /api/events?source=&project=&folder=&limit=` - live
`limit` clamped to `[1,200]`, default 50 (`:758-762`). Handler chain: `getEvents` `:204-214` ->
`loadEventPage` (`src/event-browser.ts:30-68`).
```json
{
  "events": [
    {
      "id": "a-2#0", "event_uuid": "a-2", "block_index": 0, "session_id": "smoke-session-2",
      "parent_uuid": "u-2", "timestamp": "2026-08-30T00:01:01.000Z", "project": "lanceglass",
      "envelope_type": "assistant", "block_type": "text", "semantic_role": "assistant_answer",
      "tool_name": "", "tool_use_id": "", "is_error": false,
      "text": "Yes. The source-file manifest skips the completed batch on resume.",
      "text_hash": "5c79dabaccd507f1c65b8fc55114039f10eb82648506de40b7ab8d5123fb1b47",
      "source": "fixture",
      "file_path": ".../fixtures/minimal/z-session.jsonl",
      "folder": ".../fixtures/minimal"
    }
  ],
  "source": "fixture", "project": "", "folder": "", "limit": 2, "total": 7,
  "facets": { "projects": [], "folders": [] }
}
```
Row shape is `EventRow` (`src/types.ts:8-25`) plus `file_path`/`folder` grafted on by
`loadEventPage` when a provenance path resolves (`event-browser.ts:53-58`). `facets` here is
**always the empty stub** - see the asymmetry note above.

#### `GET /api/events/facets?source=&project=` - live
Handler: `:768-772` -> `event-browser.ts:87-108` (cached per `cacheNamespace` keyed by row-count
signature so it invalidates only when table counts change).
```json
{ "source": "fixture", "project": "", "facets": { "projects": [{"value":"?","count":1},{"value":"lanceglass","count":6}], "folders": [] } }
```
`"?"` is a real, reachable value - `src/normalize.ts:297`: `project: basename(cwd) || "?"`. Any
session block whose JSONL record has no `cwd` lands in project `"?"`, not an empty string.

#### `GET /api/events/live?source=&project=&limit=` - shape
Handler `:773-781` -> `getLiveEvents` `:224-238`, backed by `db.plain.events().latestWindow()`.
Response omits `facets` entirely and `folder` is always `""`:
```json
{ "events": [ { "...EventRow": "..." } ], "source": "fixture", "project": "", "folder": "", "limit": 50, "total": 7 }
```

#### `GET /api/history?period=&date=&source=&project=&folder=` - live
`period` ∈ `day|week|month` (default `week`); `date` `YYYY-MM-DD` default *today in
`Asia/Bangkok`*. Type: `HistoryResponse` (`src/history.ts:45-65`). Captured with `period=month`,
no `date` (defaults to `2026-09-03`, matching this session's date) - fixture events are dated
`2026-08-30`, outside September, so counts are legitimately zero (illustrates the Bangkok-day
windowing, not a bug):
```json
{
  "time_zone": "Asia/Bangkok", "period": "month", "date": "2026-09-03", "anchor": "2026-09-03",
  "start": "2026-09-01", "end": "2026-09-03", "source": "fixture", "project": "", "folder": "",
  "totals": { "days": 3, "active_days": 0, "events": 0, "sessions": 0, "sources": 0, "projects": 0, "folders": 0 },
  "days": [
    { "date": "2026-09-01", "event_count": 0, "session_count": 0, "groups": [] },
    { "date": "2026-09-02", "event_count": 0, "session_count": 0, "groups": [] },
    { "date": "2026-09-03", "event_count": 0, "session_count": 0, "groups": [] }
  ]
}
```
With matching data, each `groups[]` entry is `{source,project,folder,event_count,session_count,
sessions:[{session_id,source,project,folder,started_at,ended_at,event_count,preview,
continues_before,continues_after}]}` (`history.ts:29-43`) - `continues_before/after` mark
sessions that straddle the requested window, computed via `sessionSpans` cross-referenced in
`src/server.ts:345-450`.

#### `GET /api/history/session?date=&source=&project=&folder=&session_id=&offset=&limit=` - shape
**All five of `date`, `source`, `project`, `folder`, `session_id` are required** - omitting any
throws `400 "<name> is required"` (`requiredHistoryText`, `:546-551`, called at `:557-561`).
`offset` default 0, `limit` default 200 / max 500. Type: `HistorySessionResponse`
(`history.ts:72-85`):
```json
{
  "time_zone": "Asia/Bangkok", "date": "2026-08-30", "source": "fixture", "project": "lanceglass",
  "folder": ".../fixtures/minimal", "session_id": "smoke-session-2", "offset": 0, "limit": 200,
  "total": 2, "selected_day_events": 2, "next_offset": null,
  "events": [ { "id": "u-2#0", "timestamp": "2026-08-30T00:01:00.000Z", "block_index": 0, "block_type": "text", "semantic_role": "human_intent", "tool_name": "", "text": "Can a partial import resume without duplicating earlier rows?" } ]
}
```

#### `GET /api/vectors/visualize?deployment=&date=&source=&project=&folder=&session_id=&limit=&actor=` - live
Parsed by `parseHistoryVectorRequest` (`src/history-vectors.ts:47-87`). **`deployment` is
restricted to `dual-4090` or `cloudflare` only** (`HISTORY_VECTOR_DEPLOYMENTS`, `:11`) - note
`m5-ollama` is a valid CLI/embedding deployment (§5) but is **not** one of the two values this
endpoint accepts; passing it 400s. `date`, `source` (<=128 chars), `project` (<=512, empty
allowed), `folder` (<=4096), `session_id` (<=4096) are all required; `limit` 1-500 default 200;
`actor` repeatable, values `human`/`agent` (comma-splittable), default both.

Live capture against the fixture (no embeddings run yet -> `missing_store` branch,
`history-vectors.ts:303-313`):
```json
{
  "deployment": "dual-4090",
  "scope": { "date": "2026-01-01", "source": "fixture", "project": "", "folder": "[unknown provenance]", "session_id": "x", "actors": ["human", "agent"] },
  "limit": 200,
  "space": { "id": "ollama-bge-m3-790764642607-1024-cosine-text-v1", "provider": "ollama", "model": "bge-m3", "revision": "7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab", "dimension": 1024, "distance": "cosine", "text_policy": "event.text.slice(0,2000)@v1" },
  "available": false, "status": "missing_store",
  "coverage": { "eligible": 0, "embedded": 0, "missing": 0, "sampled": 0 },
  "projection": { "method": "deterministic-pca-3d", "explained_variance": null },
  "points": [],
  "error": "No dual-4090 vector store is connected."
}
```
Note `deployment: "dual-4090"` resolves to the **same embedding space** as `m5-ollama`
(`DUAL_4090_EMBEDDING_SPACE = ACTIVE_EMBEDDING_SPACE`, `embedding-provider.ts:78`) - "verified
identical to M5 Ollama; deployment hardware is not a vector space." When a store exists and rows
are embedded, `status:"ready"` and `points[]` is
`{event_id,x,y,z,timestamp,source,project,session_id,block_type,semantic_role,tool_name,
text_preview}` (`history-vectors.ts:340-356`) - `x/y/z` come from a from-scratch deterministic
power-iteration PCA over the raw vectors (`normalizedAxes`, `:175-249`), not a stored index. A
mismatched embedding space throws `HistoryVectorStoreError` -> `422` (`:277-279`).

#### `GET /api/import/plan?source=&root=&plan_state=&compare=` - live
`plan_state` ∈ `all|actionable|new|changed|unchanged|shrunk` (default `all`); `compare` ∈
`full|metadata` (default `full` - hashes file contents; `metadata` only compares size+mtime).
Type `PlanReport` (`src/types.ts:97-108`). Captured on the second call after importing (files now
`unchanged`, ids are `sha256("<source>\0<path>")`):
```json
{
  "source": "fixture", "root": ".../fixtures/minimal", "plan_revision": "c72f0d09...4cd",
  "found": 2, "new": 0, "changed": 0, "unchanged": 2, "shrunk": 0, "will_parse": 0,
  "files": [
    { "id": "c0ea41e4...af2f6b", "source": "fixture", "path": ".../session.jsonl", "size": 1107, "mtimeMs": 1788409818803.25, "state": "unchanged" },
    { "id": "d6416544...bbea3a228", "source": "fixture", "path": ".../z-session.jsonl", "size": 480, "mtimeMs": 1788409818803.3418, "state": "unchanged" }
  ]
}
```
`plan_revision` is a stable `sha256` over `[source, root, ...sorted (id,size,mtime,state) rows]`
(`importer.ts:313-325`) - it is the value a client must echo back as `expectedPlanRevision` when
starting an async job (below), so a stale UI/agent can't import against a plan that changed
underneath it.

#### `GET /api/import/intake?source=&root=` - live
Cheap metadata-only precheck (never hashes contents, unlike `/plan`'s default `full` mode). Type
`IntakeReport` (`types.ts:110-120`):
```json
{ "source": "fixture", "root": ".../fixtures/minimal", "checked_at": "2026-09-03T04:37:20.416Z", "found": 2, "new": 0, "changed": 0, "indexed": 2, "reconcile": 0, "actionable": 0 }
```

#### `POST /api/import` - shape (synchronous, blocking)
Guards: `validateMutation` (`:648-653`), body <=16KB (`MAX_BODY_BYTES`, `:38`). Body:
```json
{ "root": "", "source": "fixture", "maxFiles": 5 }
```
`maxFiles` **required**, integer `1-100` (`:677-680`). `root`/`source` resolved by
`resolveSourceSpec` (`src/sources.ts:39-49`) - an explicit `root` wins; otherwise `source` must
match a preset id. Response is `ImportReport` (`types.ts:122-132`, matches the CLI `import`
output shown in §8) - real captured example (via CLI, identical shape):
```json
{
  "source": "fixture", "root": ".../fixtures/minimal", "plan_revision": "3108e554...b0a7",
  "found": 2, "new": 2, "changed": 0, "unchanged": 0, "shrunk": 0, "will_parse": 2,
  "selected_files": 2, "remaining_files": 0, "partial": false,
  "parsed_records": 7, "blocks": 7, "inserted": 7, "duplicates": 0,
  "occurrences_inserted": 7, "corrupt": 1
}
```
(`corrupt: 1` is real - the bundled fixture deliberately contains one malformed JSONL line to
exercise that path.) `409 {"error":"an import writer is already active","active_id":...}` if a
sync import or async job already holds the writer lock (`jobs.tryAcquireSync()`, `:806-807`) -
only one writer, sync or async, may run at a time per process.

#### `POST /api/jobs/import` - shape (asynchronous, returns immediately)
Body:
```json
{
  "mode": "batch", "root": "", "source": "claude",
  "expectedPlanRevision": "c72f0d09...4cd", "expectedWillParse": 0,
  "planPolicy": "exact", "maxFiles": 10
}
```
(`expectedPlanRevision`/`expectedWillParse` also accept snake_case aliases,
`src/server.ts:690-696`.) `mode: "all"` **forbids** `maxFiles`; `mode: "batch"` **requires** it,
`1-100` (`:704-711`). `planPolicy: "exact"` (default) pins the job to the plan revision passed in;
`"refresh"` re-plans at job start instead. Response `202`, type `ImportJob`
(`src/jobs.ts:29-46`):
```json
{
  "id": "5b1c...uuid", "kind": "import", "mode": "batch", "state": "running",
  "source": "claude", "root": "/Users/x/.claude/projects", "max_files": 10,
  "plan_revision": "c72f0d09...4cd", "expected_will_parse": 0, "plan_policy": "exact",
  "created_at": "2026-09-03T04:40:00.000Z", "started_at": "2026-09-03T04:40:00.000Z"
}
```
Internally this spawns `bun src/cli.ts import --root <root> --source <source> [--expect-plan
<rev> --expect-count <n>] [--max-files <n>]` as a **child process** (`jobs.ts:264-284`) with
`DB_DIR`/`PLAIN_DB_DIR` pinned to the server's own store - i.e. the HTTP job runner is itself a
CLI-shell-out, same as the maw plugin (§3).

#### `GET /api/jobs` - live (empty on a fresh server)
```json
{ "jobs": [], "active_id": null }
```
`jobs.list()` returns the last <=50 jobs, most-recent-first (`jobs.ts:57`, `:164-166`).

#### `GET /api/jobs/:id/log?from=` - shape
`from` non-negative integer offset, default 0. `404 {"error":"job not found"}` for unknown id.
Type (`jobs.ts:173-188`):
```json
{
  "job": { "...ImportJob": "..." }, "offset": 0, "from": 0, "next": 42, "truncated": false,
  "lines": [ { "offset": 0, "stream": "stdout", "line": "[jscan] plan complete 12/12" }, { "offset": 1, "stream": "stderr", "line": "[jscan] import progress 1/3 records=60 blocks=81" } ]
}
```
Log lines are capped at 500 retained per job and 64KB per line, both with `"… [line truncated:
N bytes]"` markers (`jobs.ts:59-60`, `:76-81`).

#### `POST /api/jobs/:id/cancel` - shape
Body must still be a valid JSON object (even `{}`). `404` unknown id; `409 "job is already
<state>"` if not `running`/`cancelling`. `202`, returns the updated `ImportJob` with
`state:"cancelling"` - sends `SIGTERM`, escalates to `SIGKILL` after a 1500ms grace window
(`KILL_GRACE_MS`, `jobs.ts:61`, `:221-234`).

#### `GET /assets/*` - path-traversal-guarded static serving
`staticFile()` (`:726-733`) resolves under `ui/dist` and rejects anything that escapes it;
`content-type` from a small extension map (`CONTENT_TYPES`, `:113-121`, else
`application/octet-stream`); `cache-control: public, max-age=31536000, immutable`.

### 1.2 Live proof of the Host-header gate
```
$ curl -s -H "Host: evil.example.com" http://127.0.0.1:4399/api/status
{"error":"requests require a local Host"}
```
Any client - including a legitimate one behind a reverse proxy that rewrites `Host` - must
present a loopback `Host` value, or every route (not just `/api/*`) 400s.

---

## 2. MCP surface - **none**

Repo-wide search, excluding `.git`:
```
grep -rliE '\bmcp\b' --include='*.ts' --include='*.tsx' --include='*.json' --include='*.md' --include='*.toml' .   -> 0 files
grep -rn 'tools/list|tools/call' --include='*.ts' --include='*.tsx' --include='*.md' .                             -> 0 matches
```
`package.json` dependencies/devDependencies (`package.json:32-50`) contain no
`@modelcontextprotocol/sdk` or similar. There is no JSON-RPC dispatcher, no `tools/list` or
`tools/call` handler, no stdio/streamable-HTTP MCP transport, anywhere in this checkout.
Lanceglass's only externally-callable surfaces are the HTTP JSON API (§1), the CLI (§8), and the
maw plugin (§3) - which is a process adapter, not a protocol server. Building an MCP tool surface
for lanceglass is new work; see §8's "Path D."

---

## 3. `maw-plugin/` - in full

Three files, no subdirectories tracked in git (`maw-plugin/dist/` is build output,
`.gitignore:5`):

```
maw-plugin/index.ts          199 lines - the plugin entry point / handler
maw-plugin/plugin.json        16 lines - the manifest maw reads
maw-plugin/streaming.test.ts 217 lines - backpressure/signal/e2e tests for the handler
```

### 3.1 Manifest - `maw-plugin/plugin.json` (verbatim)
```json
{
  "name": "jsonl-scanner",
  "version": "26.9.1-alpha.1401",
  "entry": "./index.ts",
  "sdk": "^1.0.0",
  "description": "Maw CLI adapter for the Lanceglass LanceDB importer and UI.",
  "author": "Soul-Brews-Studio",
  "cli": {
    "command": "jsonl-scanner",
    "aliases": ["jscan"],
    "help": "maw jscan <plan|import|embed|status|events|schema|ui> - use the same LanceDB core as Lanceglass"
  },
  "weight": 0,
  "license": "MIT",
  "schemaVersion": 1
}
```
`version` **must** equal `package.json#version` or the build step throws
(`scripts/build-maw-plugin.ts:10-14`) - the two are kept in lockstep on every release. This is
the entire declarative contract maw needs: a package name, an entry file, an SDK range, and one
CLI-command registration (`command` + `aliases` + a `help` string). Maw registers exactly **one**
command, `jsonl-scanner` (alias `jscan`) - every "subcommand" a user types
(`plan`/`import`/`embed`/`status`/`events`/`ui`/...) is just argv forwarded through, unknown to
maw itself.

### 3.2 Entry point - `maw-plugin/index.ts` (the plugin contract)
```ts
// :5-13
type InvokeContext = {
  source?: string;
  args?: unknown;
  writer?: (...values: unknown[]) => unknown | PromiseLike<unknown>;
  errorWriter?: (...values: unknown[]) => unknown | PromiseLike<unknown>;
  signal?: AbortSignal;
};
type InvokeResult = { ok: boolean; output?: string; error?: string };

// :23-26
export const command = {
  name: "jsonl-scanner",
  description: "Import and inspect JSONL through the Lanceglass LanceDB engine.",
};

// :129 - the actual entry point maw invokes
export default async function handler(ctx: InvokeContext): Promise<InvokeResult> { ... }
```
This **is** the plugin API: a default-exported async `handler(ctx) => {ok, output?, error?}`.
Behavior, by line:

- **`ctx.args` only trusted when `ctx.source === "cli"`** (`:146`) - anything invoking the plugin
  from a non-CLI source gets `args = []`, i.e. defaults to printing help. This is the seam maw
  would use to distinguish "a human typed `maw jscan ...`" from some other future invocation
  path.
- `subcommand = args[0] ?? "help"`; `help`/`--help`/`-h` print the static command list
  (`:110-127`) and return `{ok:true}` without touching the filesystem.
- **`projectRoot()`** (`:30-41`) locates the real lanceglass checkout two ways: (a) dev mode - if
  `../src/cli.ts` exists relative to this file, use that directory directly; (b) installed mode -
  read a sibling `project-root.txt` marker (an absolute path written at build time, see 3.3) and
  verify `<that path>/src/cli.ts` exists. This is how an *installed* plugin copy (living under
  maw's own plugin directory) finds and runs the real source tree instead of vendoring the whole
  app.
- **`ui` subcommand** (`:154-166`): runs `bun run ui:build` in the project root first (streaming
  its output), then spawns `bun src/server.ts` with `PORT` set from `--port` (falls back to
  `process.env.PORT` or `"4320"`) - i.e. `maw jscan ui` boots the exact same server documented in
  §1, long-running, streamed until killed.
- **Everything else** (`:168`): spawns `bun src/cli.ts <...args>` in the project root, inheriting
  the parent's full `env`, and streams stdout/stderr **line-by-line** - `forward()` (`:48-65`)
  buffers partial reads and only calls `emit(line)` on complete lines. Each `emit` **awaits**
  `ctx.writer` before reading the next chunk (`:82-83` calling into `forward`), so a slow
  consumer applies real backpressure to the child rather than buffering unboundedly in memory -
  exactly what `streaming.test.ts`'s "awaits each stdout sink write before forwarding the next
  line" case (`:64-85`) and the 200-record real-CLI round-trip case (`:159-215`) verify.
- **Signal handling** (`:84-107`): the child's `SIGINT`/`SIGTERM` listeners are attached to the
  *parent* process and forwarded verbatim to the child; an aborted `ctx.signal` also
  `SIGTERM`s the child. Listeners are always removed in a `finally` (verified by
  `streaming.test.ts:139-157`, which asserts `process.listenerCount("SIGINT")` returns to its
  prior value after the handler settles).
- **`if (import.meta.main) { ... }`** (`:187-198`): when `index.ts` is executed directly (not
  imported), it self-invokes `handler({source:"cli", args: process.argv.slice(2), ...real
  stdout/stderr writers})` and sets `process.exitCode`. This means the plugin file **doubles as a
  standalone executable** - `bun maw-plugin/index.ts events --source fixture --limit 200` works
  with no maw installed at all (this is literally how `streaming.test.ts:187-189` drives its
  real end-to-end test).

### 3.3 Build/install - `scripts/build-maw-plugin.ts` (verbatim, 22 lines)
```ts
const root = join(import.meta.dir, "..");
const source = join(root, "maw-plugin");
const dist = join(source, "dist");
const project = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const manifest = JSON.parse(readFileSync(join(source, "plugin.json"), "utf8"));

if (manifest.version !== project.version) {
  throw new Error(`version mismatch: package.json=${project.version}, maw-plugin/plugin.json=${manifest.version}`);
}

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });
cpSync(join(source, "index.ts"), join(dist, "index.ts"));
writeFileSync(join(dist, "plugin.json"), JSON.stringify(manifest, null, 2) + "\n");
writeFileSync(join(dist, "project-root.txt"), root + "\n");
```
`dist/project-root.txt` is the absolute-path marker `projectRoot()` reads back at runtime (3.2).
`package.json` scripts (`package.json:29-30`):
```
maw:build   = version:check && bun scripts/build-maw-plugin.ts
maw:install = maw:build && maw plugin install maw-plugin/dist --force
```
`maw plugin install ... --force` is the actual registration call into the user's maw
installation - external to this repo. `version:check` is `bun scripts/check-version.ts`
(enforces the `package.json` ⇄ `maw-plugin/plugin.json` version match called out in
`AGENTS.md:12-17` before anything is built).

---

## 4. `skills-lock.json` - not a lanceglass extension point

Verbatim (repo root, 12 lines):
```json
{
  "version": 1,
  "skills": {
    "archify": {
      "source": "tt-a1i/archify",
      "sourceType": "github",
      "skillPath": "archify/SKILL.md",
      "computedHash": "f468f6986c2d25676bb9cd4abce9302bcd42c9983ad32b3c93d6d7be189d9988"
    }
  }
}
```
`computedHash` is a 64-hex-char digest (verified by length: `sha256`-shaped). **Nothing in this
repository reads or writes this file.** Confirmed by grepping every `.ts`/`.tsx`/`.json`/`.md`/
`.toml`/`.yml` file for `archify`, `skills-lock`, and `computedHash` - the only hit is the file
itself; it isn't referenced from `package.json` scripts, `.github/workflows/ci.yml`, or
`.gitignore`. It is a **lockfile for an external Claude-Skills-style installer** (schema:
`{version, skills: {<name>: {source, sourceType, skillPath, computedHash}}}` - fetch `skillPath`
from the `sourceType` (`github`) repo named `source`, and refuse/warn if its hash no longer
matches `computedHash`). It most plausibly pins the tooling used to *author* this repo's
architecture diagrams (`docs/lanceglass-architecture.{html,json,png}` - "archify" reads as an
architecture-diagramming skill), not anything lanceglass ships or consumes at runtime. For
integration purposes: **ignore this file** - it is a build-tooling artifact of the maintainers'
environment, not part of the product surface.

---

## 5. Extension points

Two, and only two, formal extension contracts exist. Both are **compile-time TypeScript module
registries**, not runtime plugin loaders - this is a stated, deliberate security property in both
docs (`docs/embedding-provider-plugins.md:32-35`): "Plugins are source plugins: reviewed static
imports compiled with the app. The registry never downloads or executes a remote package." There
is no dynamic `import()` by string, no filesystem directory scan, no manifest-driven plugin
discovery anywhere in `src/` or `ui/src/`.

### 5.1 Embedding provider plugin - `src/embedding-plugin.ts` + `src/embedding-plugins.ts`

```ts
// src/embedding-provider.ts:226-229
export type EmbeddingProvider = {
  readonly space: EmbeddingSpace;
  embed(texts: string[]): Promise<number[][]>;
};

// src/embedding-plugin.ts:20-25
export type EmbeddingProviderPlugin = Readonly<{
  apiVersion: typeof EMBEDDING_PROVIDER_PLUGIN_API_VERSION; // = 1
  deployment: EmbeddingDeployment;
  environment: readonly EmbeddingEnvironmentVariable[];
  create(environment: EmbeddingProviderEnvironment): EmbeddingProvider;
}>;

// src/embedding-provider.ts:25-35, :148-158
export type EmbeddingSpace = Readonly<{
  id: string; provider: EmbeddingProviderKind; model: string; revision: string;
  dimension: number; distance: "cosine" | "l2" | "dot"; textPolicy: string;
}>;
export type EmbeddingDeployment<Config = EmbeddingProviderConfigBase> = Readonly<{
  id: string; label: string; location: "local" | "lan" | "cloud"; hardware: string;
  config: Config; vectorStoreKey: string; // stable routing key: shared space => shared store
}>;

// src/embedding-plugin.ts:7-13
export type EmbeddingEnvironmentVariable = Readonly<{
  name: string; required: boolean; secret?: boolean; defaultValue?: string; description: string;
}>;
```
Constructors `defineEmbeddingSpace()`, `defineEmbeddingDeployment()`, and
`defineEmbeddingProviderPlugin()` (`embedding-provider.ts:37-55,160-181`;
`embedding-plugin.ts:27-58`) validate and `Object.freeze` every value - e.g. an
`EmbeddingSpace.id` must match `/^[a-z0-9][a-z0-9._-]*$/`, a plugin's `vectorStoreKey` must equal
its own space's `id`, environment variable names must be `SCREAMING_SNAKE_CASE`, and a `secret`
env var may not carry a `defaultValue`. **Registration is a plain array literal**:
`BUILTIN_EMBEDDING_PROVIDER_PLUGINS` (`src/embedding-plugins.ts:114-118`), three built-ins today
- `m5-ollama` (single local Ollama), `dual-4090` (round-robin/failover Ollama pool, same vector
space as `m5-ollama`), `cloudflare` (Workers AI native REST, isolated space, guarded by a
deterministic revision-fingerprint probe since Workers AI exposes no model digest -
`src/embedding-providers/cloudflare.ts:99-137`). Wrapped by
`createEmbeddingProviderRegistry(plugins)` -> the `embeddingProviderRegistry` singleton
(`embedding-plugins.ts:120-207`) exposing `.get(id)`, `.describe(env?)`, `.create(id, env?)`.

**To add a provider**: write an adapter class under `src/embedding-providers/`, give it a unique
immutable `EmbeddingSpace`, define it with `defineEmbeddingDeployment()` +
`defineEmbeddingProviderPlugin()`, and add it to the `BUILTIN_EMBEDDING_PROVIDER_PLUGINS` array -
a source change + PR, never a runtime install (`docs/embedding-provider-plugins.md:37-48` gives a
full worked example).

**Reachable only from the CLI/maw**, not HTTP: `bun src/cli.ts embed providers|probe|run`
(`src/cli.ts:260-325`) or `maw jscan embed ...`. `providers` output shape:
```json
{ "plugin_api_version": 1, "default_deployment": "m5-ollama", "deployments": [ { "id": "m5-ollama", "label": "M5 · Ollama", "location": "local", "hardware": "apple-m5", "provider": "ollama", "model": "bge-m3", "revision": "790764...", "dimension": 1024, "vector_store_key": "ollama-bge-m3-790764642607-1024-cosine-text-v1", "configured": true, "missing_environment": [], "environment": [ { "name": "M5_OLLAMA_URL", "required": false, "defaultValue": "http://127.0.0.1:11434", "description": "Preferred local Ollama base URL." } ] } ] }
```
**There is no `/api/embed*` HTTP route in `src/server.ts`** - the only HTTP touchpoint for
embeddings is the read-only `GET /api/vectors/visualize` (§1), which requires a store that
already exists. An integration that wants to *trigger* embedding must shell out to the CLI/maw,
not call the running HTTP server.

### 5.2 Vector visualization plugin - `ui/src/vector-visualization.ts` + `ui/src/vector-visualizations.ts`

This is the "pluggable vector map." Contract (`ui/src/vector-visualization.ts:1-45`):
```ts
export type VectorVisualizationPoint = {
  readonly event_id: string; readonly x: number; readonly y: number; readonly z?: number;
  readonly semantic_role: string; readonly block_type?: string; readonly text_preview?: string;
};
export type VectorVisualizationConfig = Readonly<Record<string, boolean | number | string>>;
export type VectorVisualizationConfigControl = { key: string; label: string; description?: string }
  & ( | { type: "toggle" }
      | { type: "range"; min: number; max: number; step?: number }
      | { type: "select"; options: readonly { value: string; label: string }[] } );
export type VectorVisualizationProps = {
  points: readonly Readonly<VectorVisualizationPoint>[];
  selectedEventId: string;
  onSelect: (eventId: string) => void;
  config?: VectorVisualizationConfig;
  onConfigChange?: (config: VectorVisualizationConfig) => void;
  reducedMotion?: boolean;
  onUnavailable?: (reason: string) => void;
  ariaLabel?: string;
  className?: string;
};
export type VectorVisualizationPlugin = {
  id: string; label: string; description: string; dimension: 2 | 3;
  defaultConfig: VectorVisualizationConfig;
  configControls: readonly VectorVisualizationConfigControl[];
  load: () => Promise<{ default: ComponentType<VectorVisualizationProps> }>;
};
```
`createVectorVisualizationRegistry(plugins)` (`:111-127`) validates `id` against
`/^[a-z0-9]+(?:-[a-z0-9]+)*$/`, requires non-empty `label`/`description`, `dimension ∈ {2,3}`, and
that every `configControls[].key` has a type-matching default in `defaultConfig` - then
deep-freezes everything. Registration, again a literal array
(`ui/src/vector-visualizations.ts:7-31`):
```ts
export const VECTOR_VISUALIZATIONS = createVectorVisualizationRegistry([
  { id: "3d", label: "Atlas 3D", dimension: 3, defaultConfig: { spin: false },
    configControls: [{ key: "spin", type: "toggle", label: "Auto rotate", description: "..." }],
    load: async () => ({ default: (await import("./VectorMap3D")).VectorMap3D }) },
  { id: "2d", label: "Flat 2D", dimension: 2, defaultConfig: {}, configControls: [],
    load: async () => ({ default: VectorMap2D }) },
] as const satisfies readonly VectorVisualizationPlugin[]);
```
`3d` (`VectorMap3D.tsx`, Three.js) is **lazy-loaded** via dynamic `import()` - the heavy 3D engine
never enters the bundle unless selected; `2d` (`VectorMap2D.tsx`, plain SVG, shown in full in
`ui/src/VectorMap2D.tsx:1-66`) is eager. `load()` is exactly the lazy-import boundary. Host-owned
invariants a plugin must respect (`docs/vector-visualization-plugins.md:46-54`): never overlay
coordinates across incompatible embedding spaces, apply Human/Agent actor filters before
sampling/PCA, coordinate cross-panel selection only by `event_id`, and `Atlas 3D` falls back to
`Flat 2D` on failure - never to a different embedding space. A helper,
`pointCoordinates()` (`vector-visualization.ts:129-139`), is exported for reuse - it maps
normalized `[-1,1]` x/y into the fixed 720x400 SVG viewBox `VectorMap2D` renders into.

**To add a visualizer**: implement a component accepting `VectorVisualizationProps`, add one
entry to `VECTOR_VISUALIZATIONS`, keep the `id` stable forever once shipped (History URLs encode
it) - again, a source change, never a runtime plugin drop-in.

---

## 6. `types/` directory - ambient shims, **not** the app's contract types

```
types/bun-runtime.d.ts   15 lines
types/bun-test.d.ts       8 lines
```
Full contents:
```ts
// types/bun-runtime.d.ts
declare const Bun: any;
declare namespace Bun {
  type Subprocess<_Stdin = unknown, _Stdout = unknown, _Stderr = unknown> = any;
}
interface ImportMeta {
  readonly dir: string;
  readonly main: boolean;
}

// types/bun-test.d.ts
declare module "bun:test" {
  type TestBody = () => unknown | Promise<unknown>;
  export const afterEach: (body: TestBody) => void;
  export const describe: (name: string, body: TestBody) => void;
  export const expect: any;
  export const test: (name: string, body: TestBody) => void;
}
```
These exist because the project deliberately has **no `bun-types` package** installed (verified -
`node_modules/bun-types` is absent) and `tsconfig.json`'s `"types"` array is only
`["node","react","react-dom"]` (`tsconfig.json:10`) - so these two files are hand-rolled ambient
replacements just large enough to let `tsc --noEmit` (`bun run typecheck`) see `Bun`,
`Bun.Subprocess`, `import.meta.dir/main`, and the four `bun:test` exports `src/`/`ui/src/`/
`tests/`/`scripts/` actually use. One consequence worth flagging: `tsconfig.json`'s `include`
(`:12-20`) lists `src`, `scripts`, `tests`, `ui/src`, `types`, `vite.config.ts` - **`maw-plugin/`
is not included**. `maw-plugin/streaming.test.ts` imports `beforeEach`/`spyOn` from `bun:test`,
which `bun-test.d.ts` does *not* declare - that only typechecks-clean because `maw-plugin/` is
outside `tsc`'s scan set entirely; it still runs fine under `bun test` (Bun's own runtime
transpiler doesn't need the `.d.ts` to execute, only `tsc --noEmit` would care).

**The actual exported contract types an integrator needs** live elsewhere and are all cited in
full above: request/response shapes in `src/types.ts`, `src/history.ts`, `src/history-vectors.ts`,
`src/jobs.ts`; Arrow table schemas in `src/schemas.ts`; the two plugin contracts in
`src/embedding-provider.ts` / `src/embedding-plugin.ts` and `ui/src/vector-visualization.ts`.

---

## 7. `wrangler.toml` - deploys the **demo only**, not the product

Verbatim (repo root, 9 lines):
```toml
name = "lanceglass-fixture-demo"
main = "worker/index.ts"
compatibility_date = "2026-09-01"

[assets]
directory = "./ui/dist"
binding = "ASSETS"
not_found_handling = "single-page-application"
run_worker_first = ["/api/*", "/health"]
```
Reading each line: the Worker's own code (`main = "worker/index.ts"`, the synthetic in-memory
API from §1) only runs for requests matching `run_worker_first` - `/api/*` and `/health`.
**Every other path, including `/` itself, is served directly by the static `ASSETS` binding**
(the pre-built `ui/dist` SPA) without the Worker function executing at all;
`not_found_handling = "single-page-application"` makes unknown paths fall back to `index.html`
for client-side routing. `name = "lanceglass-fixture-demo"` matches the public URL
(`lanceglass-fixture-demo.laris.workers.dev`, linked from `README.md:24`).

**Deliberately absent** (cross-checked against README's "Privacy boundary" and
`docs/README.md`'s screenshot-provenance note, both of which state this explicitly): no
`[[kv_namespaces]]`, no `[[d1_databases]]`, no `[[r2_buckets]]`, no `[[durable_objects]]`, no
`[vars]`/secrets, no `account_id`, no custom `routes`. There is **no binding of any kind to real
LanceDB or any persistence layer** - `worker/index.ts` cannot reach the real
`src/server.ts`/LanceDB engine even in principle; it regenerates 1,000 synthetic events from a
seeded array at module load (`worker/index.ts:25-53`) and its "write" endpoints
(`POST /api/import`, `POST /api/jobs/import`) return canned, deterministic reports that reset on
every reload. **This file is not evidence of how the real product is deployed** - it only proves
the public demo is safe to run with zero credentials or state.

---

## 8. Integration path - how an external tool actually gets in

Ranked by what's already load-bearing in this repo (i.e. least new glue required).

### Path A - HTTP JSON API (best for a co-resident read-mostly integration)
1. Something must already be serving `src/server.ts` (`bun run ui`, or `maw jscan ui`) - default
   `http://127.0.0.1:4320`.
2. Requests **must** use a loopback `Host` (§1.2) - run the client on the same machine, or tunnel
   in a way that preserves the `Host` header as `127.0.0.1`/`localhost`.
3. No CORS headers are ever sent (irrelevant for a non-browser client - CORS only gates browser
   JS) and there is **no auth** - anything that can reach the port can read and write.
4. Discover state with `GET /api/status`, page real rows with `GET /api/events`, pull day/week/
   month rollups with `GET /api/history`, and - once an embedding deployment has actually been
   run via the CLI (embeddings are not HTTP-triggerable, §5.1) - read projected points with
   `GET /api/vectors/visualize`.
5. To ingest fresh JSONL: `POST /api/import` for a small blocking batch (`maxFiles` <=100), or
   `POST /api/jobs/import` + poll `GET /api/jobs/:id/log?from=N` for anything long-running - echo
   back the `plan_revision` from a prior `GET /api/import/plan` as `expectedPlanRevision` so the
   job refuses to run against a plan that's gone stale underneath it.

### Path B - direct CLI (best for one-shot scripts, cron, or another agent shelling out)
```
cd <lanceglass-checkout>
bun src/cli.ts status
bun src/cli.ts events --source claude --limit 20
bun src/cli.ts plan --source claude
bun src/cli.ts import --source claude --max-files 10
bun src/cli.ts embed providers
```
Every command prints **exactly one JSON document to stdout**; all progress goes to **stderr**, so
piping to `jq` is always safe (README:109-110, verified live in §1's captures - this is precisely
how those samples were taken, using `DB_DIR`/`PLAIN_DB_DIR`/`VECTOR_DB_DIR` env vars pointed at an
isolated temp directory so nothing touched real history). This is the lowest-ceremony path and
needs no long-running process.

### Path C - the maw plugin (best if the caller is itself a maw agent)
```
bun run maw:install                       # once, registers `jsonl-scanner` / `jscan`
maw jscan status
maw jscan import --source claude --max-files 10
maw jscan ui --port 4320
```
Per §3, this is a transparent argv-forwarding proxy to `bun src/cli.ts` (or `bun src/server.ts`
for `ui`) with line-buffered, backpressure-safe stdout/stderr streaming and OS-signal forwarding.
An agent driving lanceglass through maw gets byte-identical JSON to Path B, just routed through
maw's own session/tmux plumbing instead of a raw shell - useful specifically because it can be
addressed as `maw hey <agent-name>` / `maw capture` from another orchestrating agent rather than
needing direct shell access to the target machine.

### Path D - MCP (does not exist; would be new work)
No MCP server ships anywhere in this repo (§2). To expose lanceglass to an MCP client (e.g. so a
different Claude session or Desktop could browse agent history as tools), a **new** thin server
would need to be authored, most naturally by either:
- **Shelling out per tool call** - mirror Path B: each MCP `tools/call` invokes
  `bun src/cli.ts <cmd>` and parses its one-shot JSON stdout. Simple, but pays a process-spawn per
  call and gets none of the async-job/log-streaming machinery.
- **Proxying the HTTP API** - mirror Path A: the MCP server holds (or itself spawns, the way
  `maw-plugin/index.ts` does for `ui`) a long-lived `bun src/server.ts` and translates each MCP
  tool into a `fetch()` against `127.0.0.1:<port>`, forwarding the documented JSON in §1 as the
  tool result. This keeps LanceDB warm and gets real async import jobs "for free."

Either way, the tool/resource **schemas would be authored from scratch** against the types
documented in §1/§5/§6 (`src/types.ts`, `src/history.ts`, `src/history-vectors.ts`,
`src/embedding-plugin.ts`, `ui/src/vector-visualization.ts`) - there is no existing JSON Schema,
OpenAPI spec, or tool-definition file in this repo to lift verbatim; the closest thing to a
machine-readable contract today is the TypeScript types themselves plus the two `docs/*-plugins.md`
files (§5), which are the canonical prose descriptions of the only two stable extension seams
this project actually promises to keep compatible across versions.
