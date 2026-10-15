# lanceglass - Testing, Verification and Proof Discipline

Source read from `/Users/switchaphon/ghq/github.com/Soul-Brews-Studio/lanceglass/` on 2026-09-03.
All claims below were checked against the actual repo, not summarized from docs alone: I ran
`bun install --frozen-lockfile`, `bun test`, and the full `bun run smoke` gate myself (see
"Verified claims" below) rather than trusting README prose.

## TL;DR

- 163 tests across 23 files, `bun test` (Bun's built-in runner), zero mocking libraries. I ran it: **163 pass, 0 fail, 631 expect() calls, 5.93s.**
- There is no code-coverage tool, no coverage script, no coverage CI gate. `coverage/` sits in `.gitignore` unused.
- There is no relevance/recall test and no "compare against full-text search" harness (the pattern the sibling repo `lance-indexer` reportedly has). This is not an oversight so much as a category error to check for: lanceglass does not yet ship a query-time nearest-neighbor search feature at all. What exists is embedding generation (`embedPending`) and a bounded, deterministic PCA visualization (`visualizeHistoryVectors`) for a 3D/2D scatter plot. There is nothing that ranks results by similarity to a query today, so there is nothing for a recall harness to measure yet.
- Determinism is solved by never calling a real model in tests (hand-written fake providers returning fixed vectors) and, for the one real numerical algorithm in the vector path (PCA-style projection), by seeding its power-iteration with a fixed linear congruential generator (`let seed = 42`) instead of `Math.random()` - `src/history-vectors.ts:195-198`.
- CI is a single job that runs one script, `bun run smoke`, which chains version check -> typecheck -> production UI build -> full test suite -> a real end-to-end fixture run against real spawned subprocesses and a real HTTP server. `.github/workflows/ci.yml:11-21`.
- The repo explicitly names its own smoke test "the acceptance proof" (`PRODUCT.md:46`) and documents a "Screenshot provenance" disclosure for its doc images (`docs/README.md:19-30`), extending proof discipline to visual docs, not just code.
- One claim is measured-but-not-machine-enforced: README says "163 focused tests" (`README.md:198`). That number is correct today (I reproduced it exactly), but nothing regenerates or checks it - it is hand-typed prose with no CI step comparing it to actual `bun test` output. Contrast this with the version-alignment claim, which **is** mechanically enforced every run (`scripts/check-version.ts`, wired into `smoke`).

---

## 1. Test structure and conventions

Runner: **`bun test`** (Bun's native test runner, `bun:test` import), invoked via `package.json:26`
(`"test": "bun test"`). No Jest, no Vitest, no Mocha.

Test files are **colocated by domain**, not centralized in one folder:

| Location | File count | What it covers |
|---|---|---|
| `tests/` | 11 files | backend: schemas, importer, normalize, history, embeddings, embedding-provider, embedding-cli, event-browser, event-view, jobs, vector-status |
| `ui/src/*.test.ts` | 10 files | pure frontend logic: history-date, history-sort, history-source, history-vector, job-progress, latest-request, location, plan-filter, event-facets, vector-visualizations |
| `maw-plugin/streaming.test.ts` | 1 file | the optional `maw` CLI adapter's stdout/stderr streaming |
| `worker/index.test.ts` | 1 file | the static Cloudflare Worker demo |

11 + 10 + 1 + 1 = 23 files, which is exactly what `bun test` reported ("Ran 163 tests across 23
files"), confirming discovery is a flat `*.test.ts` glob across the whole repo, not an allowlist.

**Naming convention**: `describe()` blocks name a subsystem or invariant category; `test()` names
are full sentences describing an observable behavior or guarantee, not "test 1" / "should work".
Examples (`tests/embeddings.test.ts:100-596`):

- `"rejects another embedding space before creating vector storage"`
- `"does not disguise a non-ENOENT vector filesystem error as a missing store"`
- `"persists completed vector batches and resumes from the plain store after failure"`
- `"uses a token-owned vector lock so a contender cannot delete another writer's lease"`

These names are effectively the spec. A reader can `grep -n "test(\"" tests/*.ts` and get a prose
list of every guarantee the system makes (I did this for `tests/*.test.ts` - see the grep output
used to build this document).

**No shared test-utility module.** Every backend test file re-declares its own `temporaryDirectories`
array plus `afterEach(() => rm(..., {recursive:true, force:true}))` cleanup, and its own local
fixture builders (`temporaryStores()`, `event()`, `occurrence()`, `vector()`, `provider()` -
e.g. `tests/embeddings.test.ts:27-98`, repeated with local variants in `tests/history-vectors.test.ts:21-95`
and `tests/vector-status.test.ts:8-31`). Six of the eleven `tests/*.ts` files independently define a
`temporaryDirectories` + `afterEach` pair (confirmed by grep). This is a deliberate tradeoff: every
test file is self-contained and can be read/copied without chasing an import chain, at the cost of
~30 lines of boilerplate duplicated six times. Given `CONTRIBUTING.md:17` ("Add or update a focused
regression test"), the duplication looks intentional - optimizing for "one file tells the whole
story" over DRY.

**Integration-heavy, not unit-heavy.** A large fraction of tests spawn the real CLI as a subprocess
(`Bun.spawn(["bun", "src/cli.ts", ...])`) against a real temp-dir LanceDB, or boot the real HTTP
server (`Bun.spawn(["bun", "src/server.ts"], ...)`) and hit it with `fetch()`. Examples:
`tests/embeddings.test.ts:598-683` (CLI + fake Ollama HTTP server), `tests/vector-status.test.ts:76-122`
(real server + malformed vector store), `tests/history-vectors.test.ts:355-403` (real server, checks a
400 on an unsupported deployment). This means "unit test" and "integration test" are not separated
into different directories or run tiers - they live side by side in the same file, gated by the same
`bun test` command.

## 2. `fixtures/` - synthetic data and the privacy boundary

Only two files exist: `fixtures/minimal/session.jsonl` and `fixtures/minimal/z-session.jsonl`.
Both are hand-written, not captured/scrubbed from a real transcript:

- `session.jsonl` (6 lines): a `user` turn, an `assistant` turn with a `tool_use` block, a
  `tool_result`, a `summary` line, a `progress` line, and a final **deliberately malformed** line
  (`{deliberately corrupt smoke line`, no closing brace, `fixtures/minimal/session.jsonl:6`) used to
  prove the parser reports `corrupt: 1` instead of crashing (`scripts/smoke.ts:82-83`).
- `z-session.jsonl` (2 lines): named to sort **after** `session.jsonl` alphabetically, which exists
  specifically to exercise "second file in a batch" / resume ordering in the smoke run and in
  `tests/importer.test.ts`.

Every field is synthetic: `cwd` is `/demo/lanceglass`, session IDs are `smoke-session` /
`smoke-session-2`, content is a canned Q&A about the tool's own import logic ("How do we import JSONL
and know whether it is new?"). This is the "why synthetic rather than real transcripts" answer: the
fixture text is written to be self-referential/on-topic filler, cheap to reason about, and safe to
publish, not a redacted real session.

The privacy boundary is stated in several places and is consistent across them:

- `AGENTS.md:7-8`: "Never commit real JSONL histories, `.data/`, credentials, or generated maw
  checkout markers."
- `AGENTS.md:33-36` ("Public-safety rule"): "Use synthetic fixture names and generic paths such as
  `/Users/example`. Do not paste captured session contents, private repository names, LAN addresses,
  tokens, account IDs, or local absolute checkout paths into source, tests, docs, images, or commit
  messages."
- `CONTRIBUTING.md:12-13`: "Do not use private session data in a reproduction. Extend
  `fixtures/minimal` or create synthetic records in a temporary directory instead."
- `SECURITY.md:13-24` ("Before publishing a fork"): a `git grep` over the **entire commit history**
  (`git rev-list --all`), not just the working tree, for home-directory paths, private-key headers,
  and bearer tokens, plus: "Placeholder tokens in tests must be obviously synthetic and must assert
  that secrets are redacted from errors and output." That last sentence is a testing rule, and it is
  enforced in practice - see `tests/embedding-provider.test.ts:403-433` ("reports Cloudflare failures
  without exposing credentials"), which asserts the error message contains `[REDACTED]` and explicitly
  `.not.toContain("do-not-leak")`.
- The privacy discipline extends to **images**, not just code: `docs/README.md:19-30` ("Screenshot
  provenance") discloses that the UI gallery screenshots were captured from a disposable database
  under `/tmp/lanceglass-public-demo` using only the repo's synthetic fixture plus "two synthetic
  long-form messages for vector-map proof," and states plainly that no personal history, credentials,
  or private paths appear in the images. This is the same "prove it, then say so" pattern applied to
  documentation assets instead of code.
- `ui.gitignore`-equivalent: `.gitignore:1,7-9` excludes `.data/`, `.env`, `.env.*` (with `.env.example`
  explicitly un-ignored on line 10) and `.wrangler/`.

## 3. Search quality verification - what exists, and the actual gap

I grepped `src/`, `tests/`, `ui/src/`, and `worker/` for `recall|precision|relevance|full-text|fts|
bm25|nearest.?neighbor|semantic search|ann index|ivf_pq|search\(` (case-insensitive). The only two
hits were `Precision` as an Apache Arrow `DataType` import in `src/database.vector.ts:3,97` -
unrelated to search quality. There is **no** relevance test, no recall/precision measurement, and no
comparison harness against full-text search anywhere in this repo.

This is worth stating precisely rather than just flagging as "missing," because the reason is not
negligence: **lanceglass does not currently implement query-time nearest-neighbor search at all.**
I confirmed this by grepping `src/*.ts` for `vectorSearch|nearestTo|\.search\(|createIndex|IVF|
withParams` - zero hits. The two vector-related capabilities that exist are:

1. **Embedding generation** (`embedPending` in `src/embeddings.ts`, exercised by
   `tests/embeddings.test.ts`) - turns eligible plain-store rows into vectors and writes them to a
   separate `event_vectors` LanceDB table. This is write-path only; nothing reads it back by query.
2. **Bounded visualization** (`visualizeHistoryVectors` in `src/history-vectors.ts:271-378`) - given
   an *exact* scope (one calendar date, source, project, folder, session, actor set, and a hard
   `limit <= 500` from `MAX_HISTORY_VECTOR_POINTS`, `src/history-vectors.ts:13`), it pulls every
   vector in that scope and projects it into 2D/3D coordinates for a scatter plot
   (`docs/README.md`'s "Vector map" feature; `README.md:152`: "scoped 2D or 3D PCA projection across
   selected vector spaces"). This is a coverage/exploration view (it reports
   `{eligible, embedded, missing, sampled}` counts, `tests/history-vectors.test.ts:200,220,283-287`),
   not a ranked-by-similarity-to-a-query search.

`lessons/08-optional-embeddings.md:8` says the vector store exists for "only explicit embedding or
future semantic search" (emphasis on *future*) - the docs themselves flag ranked semantic search as
not-yet-built. So the sibling repo's "just compare" pattern (a harness that runs the same query
through vector search and full-text search and diffs the results for recall) has nothing to attach
to here yet: there is no query API to run it against. If/when lanceglass adds a `search(query: string)`
entry point, this would be the first place a recall harness becomes meaningful, and today's absence
should not be read as "they skipped testing it" but as "the feature it would test doesn't exist yet."

What *is* tested rigorously in place of search quality is **coverage accounting and geometric
correctness** of the visualization: exact eligible/embedded/missing/sampled counts under folder
scoping (`tests/history-vectors.test.ts:148-227`), correct actor-role filtering
(`tests/history-vectors.test.ts:229-297`), bounded coordinate ranges (`Math.abs(point.x) <= 1`,
`tests/history-vectors.test.ts:213-217`), and an explicit typed empty state (`status: "missing_store"`)
rather than a silent fallback when the selected embedding space has no store
(`tests/history-vectors.test.ts:299-320`, `354-403`).

## 4. Mocking patterns for embeddings

No mocking library (no `sinon`, no `vi.mock`, no `jest.mock`) - Bun's `bun:test` ships `spyOn` and
tests otherwise use plain hand-written substitutes. Four distinct patterns, by layer:

**a) Fake `EmbeddingProvider` objects (unit level).** The core embedding logic (`embedPending`) is
tested against a hand-built provider whose `embed()` returns deterministic vectors with no network
call at all:

```ts
// tests/embeddings.test.ts:88-98
function vector(seed: number) {
  const result = Array.from({ length: EMBEDDING_DIMENSION }, () => 0);
  result[seed % EMBEDDING_DIMENSION] = 1;   // one-hot vector, cheap and deterministic
  return result;
}
function provider(embed: (texts: string[]) => Promise<number[][]>): EmbeddingProvider {
  return { space: ACTIVE_EMBEDDING_SPACE, embed };
}
```

Every embedding-pipeline test (batching, resume-after-failure, retry/backoff, date/project/folder
scoping, lock contention) is written against this fake, e.g.
`tests/embeddings.test.ts:355-382` simulates a provider that throws on its 2nd call to prove partial
batches persist and resume correctly, and `tests/embeddings.test.ts:384-403` proves retry uses an
injected `sleep` function (not real timers) so the test doesn't actually wait.

**b) Fake HTTP servers that speak the real provider protocol (contract level).** For the actual
adapters (`OllamaPoolEmbeddingProvider`, `CloudflareWorkersAIProvider`), tests spin up real
`Bun.serve()` HTTP servers on port 0 that imitate Ollama's `/api/tags` + `/api/embed` shape or
Cloudflare's `/accounts/:id/ai/run/:model` shape, and point the real adapter code at them -
`tests/embedding-provider.test.ts:145-181` (load balancing across two fake Ollama endpoints),
`:228-278` (fails over a 503 from one shard), `:280-317` (refuses a model whose `/api/tags` digest
doesn't match, proving revision-pinning without a real model), `:339-401` (Cloudflare transport,
asserting the exact request path/auth header/body shape sent). This is "test the adapter for real,
fake only the network," as opposed to (a) which fakes the whole provider interface.

**c) `spyOn(Bun, "spawn")` for process-streaming logic.** `maw-plugin/streaming.test.ts:1-15` and
`worker/index.test.ts` spy on `Bun.spawn` itself and hand back fake `Subprocess`-shaped objects with
manually-controlled `ReadableStream` controllers (`completedChild()`, `runningChild()` helpers,
`maw-plugin/streaming.test.ts:17-60`), so stdout/stderr chunking, UTF-8 split-boundary decoding, and
`kill()`/signal behavior can be tested without ever running a real child process.

**d) Direct handler invocation for the Cloudflare Worker.** `worker/index.test.ts:12-13` calls
`demoWorker.fetch(new Request(...), env)` in-process, with a fake `env.ASSETS.fetch` stub
(`worker/index.test.ts:4-10`) - no `wrangler dev`, no real Worker runtime, just the exported fetch
handler called as a function.

**Credential handling inside mocks is itself tested.** `tests/embedding-provider.test.ts:466-491` and
`:554-574` assert that provider-registry descriptions never leak the secret values passed in
(`expect(JSON.stringify(descriptions)).not.toContain("secret-token")`), and that a plugin definition
with a `secret: true` environment variable **must not** declare a `defaultValue`
(`tests/embedding-provider.test.ts:554-566`, matching the rule in `SECURITY.md:22-24`).

## 5. Determinism - how vector output is made testable at all

Two separate mechanisms, because there are two separate things that could be non-deterministic:

**a) The embedding model itself is never invoked.** Since every test substitutes a fake
`EmbeddingProvider` (section 4), model non-determinism (different vector per run, hardware-dependent
floating point, network latency) simply never enters the test suite. This sidesteps the "make an ML
model's output testable" problem entirely rather than solving it.

**b) The one real numerical algorithm - the PCA-style 3D/2D projection - is seeded, not random.**
`src/history-vectors.ts:175-198` implements `normalizedAxes()`. Its power-iteration starting vector
is generated by a fixed linear congruential generator instead of `Math.random()`:

```ts
// src/history-vectors.ts:195-198
let seed = 42;
() => {
  seed = (seed * 1_103_515_245 + 12_345) & 0x7fffffff;
  return seed / 0x7fffffff - 0.5;
}
```

Because the seed is a hardcoded literal (`42`), the projection is a pure function of its input
vectors: same vectors in, byte-identical coordinates out, every run, every machine. Tests assert this
directly rather than assuming it:

- **Repeat-call stability**: `tests/history-vectors.test.ts:174-175,218` calls
  `visualizeHistoryVectors` twice with identical input and asserts `first.points).toEqual(second.points)`.
- **Insertion-order independence**: the same test builds a second database with the *same* rows
  inserted in reverse order and vectors upserted in reverse, and asserts
  `first.points).toEqual(reorderedResult.points)` (`tests/history-vectors.test.ts:177-219`) - proving
  the projection doesn't accidentally depend on LanceDB physical row order.
- **Client-side merge determinism**: `ui/src/history-vector.test.ts:48-65` tests
  `mergeVectorEvidence` "deterministically regardless of response completion order" - merging results
  from two embedding deployments that can race, sorted to a stable output order regardless of which
  HTTP response lands first.
- Determinism is a named concern outside the vector path too: `tests/normalize.test.ts:150`,
  `"isolates file state and is deterministic across audit/write passes"`.

Net effect: nothing in this suite depends on wall-clock time, real randomness, or a real model, so
`bun test` is fully reproducible byte-for-byte between runs (I ran it twice - see below - identical
pass count both times, and the smoke run's own vector-adjacent assertions never flaked).

## 6. CI configuration (`.github/workflows/ci.yml`)

The entire file is 21 lines. One job, one step of substance:

```yaml
on:
  push: { branches: [main] }
  pull_request:
permissions:
  contents: read
jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
        with: { bun-version: 1.3.14 }
      - run: bun install --frozen-lockfile
      - run: bun run smoke
```

Notable properties:

- **No matrix.** One OS (ubuntu-latest), one Bun version (pinned exactly: `1.3.14`), no Node.js
  fallback, no Windows/macOS runners.
- **No separate jobs for lint/typecheck/test/build.** All of that is folded into the single
  `bun run smoke` script chain (`package.json:28`:
  `version:check && typecheck && ui:build && test && scripts/smoke.ts`), so there is exactly one
  green/red signal per commit, not five. A contributor cannot get "tests pass but typecheck is
  broken" as a partial-success CI state - it's all-or-nothing by construction.
- **`--frozen-lockfile`** on install, matching the exact instruction given to contributors in
  `CONTRIBUTING.md:7-9`, so CI and a fresh clone run the identical dependency graph.
- **15-minute timeout**, generous for what actually runs (see timing below).
- **No coverage upload, no artifact upload, no caching step** - nothing beyond checkout, bun setup,
  install, run.
- `permissions: contents: read` is the only permission granted - no write-back to the repo, no
  ability to push a badge/coverage-comment from CI.

## 7. Coverage approach

There is none. Specifically, I checked:

- `package.json` scripts (`package.json:20-30`): no `coverage` script.
- `bunfig.toml`: does not exist in the repo at all (confirmed by `find`), so `bun test` runs with
  Bun's default coverage settings, i.e. off.
- `.github/workflows/ci.yml`: no `--coverage` flag anywhere, no coverage-reporting action, no
  Codecov/Coveralls integration.
- `.gitignore:6` does list `coverage/` - the only trace of the concept in the whole repo - but
  nothing produces that directory. It reads as defensive habit (or leftover from a template) rather
  than an active practice.

The project's proof discipline is entirely **behavioral/scenario-based** (see section 1 - specific
named invariants, integration-level subprocess/HTTP tests) rather than **percentage-based**. Given
how much of the suite is real-subprocess/real-server integration testing against a real embedded
LanceDB, a line-coverage percentage would likely be a poor proxy for confidence here anyway (a
single `embedPending` call inside one test can execute a large fraction of the embedding module's
lines while only proving one behavior). That's a plausible reason the project didn't bother, but it
is not stated anywhere in the docs - I'm inferring it from the shape of the suite, not quoting a
rationale.

## 8. Especially: how this repo verifies its own documented claims

This is the strongest part of the repo's discipline, and it's worth separating "mechanically
enforced every run" from "true when last written, not re-checked."

### Mechanically enforced every run

- **Version alignment.** `AGENTS.md:12-18` claims `package.json#version` and
  `maw-plugin/plugin.json#version` must always match, in a specific CalVer shape
  (`YY.M.D[-alpha.HMM|-beta.HMM]`, Asia/Bangkok calendar). This is not just prose - `bun run
  version:check` (`package.json:27`) runs `scripts/check-version.ts`, which parses both files, checks
  the CalVer shape with a regex (`scripts/check-version.ts:11`), and throws if the plugin version
  differs from the package version (`scripts/check-version.ts:16-20`). It's the first step of `smoke`
  (`package.json:28`), so a version-drift PR fails CI before typecheck even runs.
- **The 9-stage smoke run matches its own description exactly.** README says the smoke gate "builds
  the production UI, creates isolated temporary databases, normalizes only the bundled fixtures,
  imports a partial batch, resumes through HTTP, proves idempotency, checks history/vector
  boundaries, and serves the built application" (`README.md:71-74`). `scripts/smoke.ts` numbers its
  own stages `[smoke 01/09]` through `[smoke 09/09]` (`scripts/smoke.ts:49,52,76,80,85,129,175,189,300`)
  and each stage's `check()` calls assert an exact, named fact - not "no exception thrown" but things
  like `check(first.inserted === 5 && first.corrupt === 1, "first batch inserts first fixture")`
  (`scripts/smoke.ts:118`) and `check(finalStatus.tables.events === 7, "seven canonical events")`
  (`scripts/smoke.ts:221`). Every `check()` failure names exactly which claim broke.
- **Provider-plugin contract checklist.** `docs/embedding-provider-plugins.md:37-48` tells a
  contributor adding a new embedding provider to add six *specific categories* of test: "transport,
  credential-redaction, output-shape, revision-mismatch, registry, and isolated-vector-store tests"
  (`docs/embedding-provider-plugins.md:46-47`), then run `bun run smoke`. I checked this against the
  actual Cloudflare provider's tests and every category is represented:
  transport = `tests/embedding-provider.test.ts:339-401`; credential-redaction = `:403-433`;
  output-shape = `:319-337`; revision-mismatch = `:435-464`; registry = `:466-491`; isolated-vector-store
  = `tests/embeddings.test.ts:119-155`. The doc's checklist isn't aspirational - it describes tests
  that actually exist for the one provider the repo ships beyond Ollama.
- **Secret redaction is asserted, not assumed.** `SECURITY.md:22-24` states the rule; the test that
  enforces it is `tests/embedding-provider.test.ts:403-433`, which passes a token literally named
  `"do-not-leak"` and asserts it never appears in a thrown error message.

### Measured once, not re-verified (the actual gap)

- **README.md:198-199**: *"`bun run smoke` is the release gate. It currently covers 163 focused tests
  plus a nine-stage end-to-end fixture run."* The "nine-stage" half is true by construction (it's
  literally numbered in the script, see above). The **"163" half is a plain hand-typed number** - I
  grepped the entire repo (`src/`, `tests/`, `ui/`, `scripts/`, every `*.md`, the CI YAML) for `163`
  and it appears in exactly these two README lines and nowhere else. There is no script under
  `scripts/` (only `build-maw-plugin.ts`, `check-version.ts`, `smoke.ts` exist) that reads `bun test`'s
  own summary line and cross-checks it against the README, and CI does not fail if someone adds or
  removes a test without updating that sentence. **I verified the number is currently correct** (see
  "Verified claims" below), but the mechanism that keeps it correct is "a human remembered to update
  it," not a computer. This is the one clear instance of "measured-then-asserted-in-prose" rather than
  "measured every run" in an otherwise unusually rigorous repo.
- Screenshot provenance (`docs/README.md:19-30`) is a similar shape: a true, specific, falsifiable
  claim about how the images were produced, but it's a paragraph of prose next to the images, not
  something CI checks (e.g. nothing verifies the screenshots were regenerated after a UI change, or
  that they still match the current build).

### Verified claims (what I reproduced myself rather than trusted)

Since this whole document is about proof discipline, I held myself to the same standard rather than
transcribing README/PRODUCT.md claims verbatim:

```
$ bun install --frozen-lockfile
81 packages installed [6.95s]

$ bun test
bun test v1.3.13 (bf2e2cec)
 163 pass
 0 fail
 631 expect() calls
Ran 163 tests across 23 files. [5.93s]

$ bun run smoke
$ bun scripts/check-version.ts
Lanceglass v26.9.1-alpha.1401
$ tsc --noEmit                 (clean, no output)
$ vite build                   (succeeds, 34 modules, ui/dist emitted)
$ bun test                     163 pass / 0 fail (again, same count)
[smoke 01/09] choose database
[smoke 02/09] create isolated database
[smoke 03/09] inspect explicit schema + repository boundary
[smoke 04/09] normalize fixture without database writes
[smoke 05/09] plan two files with stderr progress, then import one-file batch
[smoke 06/09] prove partial state before resume
[smoke 07/09] resume through HTTP import API
[smoke 08/09] repeat safely and read final rows
[smoke 09/09] serve the production React + Tailwind build
SMOKE PASS - events=7 - partial_remaining=1 to 0 - repeat_inserted=0 - db=/var/folders/.../lanceglass-smoke-.../lancedb
```

This independently confirms: the "163 focused tests" figure (exact match), the "nine-stage"
figure (exact match, and every stage name matches the source), the version-alignment claim
(`v26.9.1-alpha.1401` in both `package.json` and `maw-plugin/plugin.json`), and that the whole
public gate genuinely passes clean on an unmodified checkout - it is not a claim I had to take on
faith. Note the runtime was Bun 1.3.13 locally versus 1.3.14 pinned in CI (`.github/workflows/ci.yml:19`)
- close enough to pass here, but it means my local run is not byte-identical proof of the pinned-CI
path, only of the script's own logic.

## Practices worth copying

1. **One gate, chained, not parallel jobs.** `bun run smoke` = version check + typecheck + build +
   test + real e2e, in one script, so there is one pass/fail signal and no "tests green, build red"
   ambiguity. Easy to adopt in any Bun/Node project via a single `package.json` script.
2. **Name tests as claims, not cases.** `"does not disguise a non-ENOENT vector filesystem error as a
   missing store"` tells you what breaks if it fails. `"test 4"` does not.
3. **Fake at the interface, test the adapter for real.** Core logic (`embedPending`) is tested against
   a trivial hand-written provider (fast, deterministic, no library). The actual HTTP adapters are
   tested against real `Bun.serve()` stand-ins that speak the real wire protocol, catching shape bugs
   the trivial fake would never catch. Two tiers, matched to what each is supposed to prove.
4. **Seed pseudo-randomness with a literal constant, and assert order-independence explicitly** for
   any "derived from possibly-reordered rows" computation, not just assume it. The
   insertion-order-reversed test (`tests/history-vectors.test.ts:177-219`) is a specific, cheap,
   high-value regression guard that many projects skip.
5. **State the credential-safety test rule in the security doc, then actually write the test that
   checks it** (`SECURITY.md:22-24` <-> `tests/embedding-provider.test.ts:403-433`). Docs and tests
   cite each other's existence.
6. **Disclose how documentation screenshots/demo data were produced**, with enough detail (disposable
   DB path, synthetic-only inputs) that the claim "no real data leaked" is falsifiable, not just
   asserted (`docs/README.md:19-30`).
7. **Publish the exact test categories a new plugin author must add** (`docs/embedding-provider-plugins.md:46-47`),
   as a checklist tied to the interface contract, not a vague "add tests."

## Untested / unverified claims and gaps a reader should know about

1. **"163 focused tests" is prose, not a checked invariant** - correct today, silently goes stale the
   moment someone adds/removes a test without hand-editing `README.md:198`. (See section 8.) Cheapest
   fix would be a one-line script comparing `bun test`'s summary count against a README anchor,
   wired into `smoke`.
2. **No relevance/recall testing for vector search - because there is no query-time vector search
   feature yet.** Don't mistake this repo's vector coverage for "semantic search is tested"; what's
   tested is embedding-write correctness and visualization-projection correctness. If ranked search
   is added later, this is the gap to close first.
3. **No coverage measurement at all**, so "how much of `src/` do these 163 tests actually exercise"
   is not a question this repo can currently answer quantitatively - only qualitatively, by reading
   test names against source files.
4. **`tsc --noEmit` passing is a weaker guarantee here than it looks.** `types/bun-runtime.d.ts:1-3`
   declares `Bun` as `any` globally, and `types/bun-test.d.ts:5` declares `expect: any`. This is a
   pragmatic choice (no `@types/bun`/`bun-types` dependency at all - absent from both `dependencies`
   and `devDependencies` in `package.json`), but it means typecheck cannot catch a misused `Bun.*` API
   or a wrongly-shaped `expect(...)` assertion; only the application's own `src/` types are checked
   with real precision.
5. **My local run used Bun 1.3.13; CI pins 1.3.14** (`.github/workflows/ci.yml:19`). I did not verify
   the smoke gate against the exact pinned patch version - a reader who wants byte-for-byte CI parity
   should match that version rather than trust my local run for that specific detail.
