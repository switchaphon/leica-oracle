# Applying lanceglass to Oracle memory

> Written by Leica, 2026-09-03, after deep-learning `Soul-Brews-Studio/lanceglass`
> and surveying the 12-repo memory constellation Nat published 2026-08-29..09-02.
> Every number below was measured on mba today, not quoted from a README.

## 1. What lanceglass actually is

A local-first importer that turns append-only Claude Code / Codex JSONL into a
typed LanceDB you can inspect, with three deliberate separations:

| Separation | What it buys |
|---|---|
| **plain store vs vector store** (two physical LanceDB dirs) | Import never contacts an embedding service. If the model server is down, import still completes. Vectors are derived data and rebuildable. |
| **canonical event vs occurrence vs file** (three tables, three id schemes) | The event survives a file move. The same content seen in two files adds an occurrence, not a duplicate. |
| **inspection vs mutation** (`plan` is read-only, `import` writes a bounded batch) | You can always ask "what would change?" without changing anything. |

Identity, from `src/normalize.ts:291,310-318` and `src/importer.ts:190`:

```
events.id        = `${event_uuid}#${block_index}`                       content-derived
event_sources.id = sha256(event.id + source + file_path + line + hash)  an observation
source_files.id  = sha256(source + "\0" + path)                         the observed file
```

## 2. The state of our memory, measured today

### 2a. What works

FTS5 lexical search over `~/.oracle/oracle.db` works. `MATCH 'vec0'` -> 11 hits,
`MATCH 'measurement'` -> 39 hits. Tokenizer is `porter unicode61`.

I also tested Thai with a positive control rather than trusting a zero: "ชำระ"
occurs 1391 times in the indexed content, and both `MATCH 'ชำระ'` and
`LIKE '%ชำระ%'` return the same 1 document. **Thai search is not broken here** -
our corpus simply contains almost no Thai (35 rows). The trigram tokenizer that
`session-search` relies on IS available on this sqlite if we ever need it.

### 2b. What does not

```
oracle_documents                                     258 rows, all type=learning
  resolve to a real file                                  34    (13%)
  anchored to a project, file not there                  201
  no project anchor at all                                23

oracle_memories                                        0 rows
vectors.db  oracle_knowledge_bge_m3_meta               0 rows
            oracle_knowledge_bge_m3_vec_rowids         0 rows
```

Two separate failures, and it matters that they are separate:

**(i) The pointers are derived, not observed.** `source_file` is a title slug
truncated at ~50 characters (measured: lengths cluster 44-50, hard ceiling 50).
The file on disk was often written under a different name, so the pointer was
born dangling:

```
index: 2026-08-14_choosing-what-to-measure-outranks-measuring-it-wel.md
disk:  2026-08-14_measuring-the-wrong-operation.md
```

Repo renames add more: 64 rows point at `pops-clinic-oracle`, 15 at
`pawrent-oracle` - both renamed in July.

**(ii) Semantic search has still never run.** Correcting my own note from
2026-09-02: it claimed `vectors.db` had "no `_vec` table at all". That is no
longer true - the vec0 shadow tables now exist (embedder identity stamped
2026-09-01T16:29), so **vec0 loads fine now**. But every table has 0 rows,
`~/.ollama` is still absent, and no embedder is configured. The blocker moved
from "the extension cannot load" to "nothing has been embedded."

### 2c. Coverage

```
indexed:   258 documents, learnings only
not indexed: retrospectives 165, learn 158, inbox 44, lab 15, outbox 4, archive 5
JSONL session history: 513 files, 484 MB - indexed by nothing at all
```

## 3. Does lanceglass work on our data? Verified, not assumed

```
bun src/cli.ts plan --source claude
  -> found: 513, new: 513, will_parse: 513      wrote nothing (store dir absent)
```

513 matches my own `find` count exactly - it sees **every tier**, including the
254 files a `<project>/*.jsonl` glob misses (50.5% of our corpus: 259 tier-1,
175 subagent, 79 vercel-plugin).

```
import --root <leica project dir> --max-files 3
  -> 292 records, 132 blocks, 132 inserted, 0 corrupt
re-run identical command
  -> unchanged: 3, advanced to next batch, 498 events total, 0 duplicates
```

Idempotency holds on our real data. First attempt returned `blocks: 0` because
alphabetical ordering selected 10 `vercel-plugin/skill-injections.jsonl` files,
which carry no `type` field and are not transcripts - correct skipping, not a bug.

Compatibility: Bun 1.3.13 meets the 1.3+ requirement. `@lancedb/lancedb` is a
native binding, so there is **no `loadExtension()` anywhere** - it structurally
cannot hit the bun:sqlite bug we filed as issue #3046.
`maw-plugin/index.ts:187` carries the `import.meta.main` guard, so it will not
silently no-op under maw-rs.

## 4. What I would take, in order of value

### Take now, costs nothing but discipline

1. **Record observed paths, never derived ones.** This is the whole 87% failure.
   An `occurrence` row written at the moment of reading, carrying file path, line
   and content hash, cannot be born dangling.
2. **Content-hash identity, not title-slug identity.** A learning renamed is the
   same learning. `sha256(content)` says so; a truncated slug does not.
3. **Progress on stderr, report on stdout.** Cheap, and makes any long Oracle
   operation pipeable and non-frozen-looking.
4. **A `plan` verb before every `import`.** "What would change?" answerable
   without changing anything.

### Take next, real work

5. **Split our vector store from our knowledge store.** Today one `oracle.db`
   plus a `vectors.db` that shares its lifecycle. The lanceglass rule - each
   incompatible embedding contract gets its own *physical* store, and the model
   revision is pinned in the schema metadata - is what makes a re-embed safe.
6. **Index the other 406 markdown files**, and stop pretending learnings are the
   whole brain.
7. **Index the 513 JSONL files.** This is the part we have never had. lanceglass
   does it today, on our machine, verified above.

### Decide, do not drift

8. **Semantic search: pick a provider or close the question.** lanceglass has
   Cloudflare Workers AI and Ollama adapters behind one `EmbeddingProvider`
   interface. Cloudflare needs no local install. The current state - machinery
   present, zero rows, no provider - is the worst of both: it looks configured
   and returns nothing.

## 5. The rules worth stealing verbatim

From `DESIGN.md`, and they are not about UI:

- **The CLI Is the Evidence Rule** - the browser never invents progress; it shows
  the same process output. We have written retrospectives from agent summary
  strings before. This rule is the fix.
- **The Visible Window Rule** - a chart summarises only the window it returned,
  and must say so.
- **The Calendar Is Evidence Rule** - zero-work days stay visible. Absence is a
  finding, not a gap to delete. This is `memory-horizon`'s whole thesis too.
- **The Spaces Never Blur Rule** - compare embedding spaces side by side, never
  silently fall back across them.

## 6. Sibling repos that matter to us

- **memory-horizon** - classifies work memory as LIVE / COOLING / DORMANT /
  STALE / DEPRECATED / **LOST**. Our 224 unresolvable rows are LOST by its exact
  definition. Read this next; it gives us vocabulary for a problem we can already
  measure.
- **psi-memory-open** - the only tool in the family built for *markdown ψ vaults*,
  which is what our written memory actually is. lanceglass handles the JSONL half;
  this handles the other half.
- **session-search** - the one with an MCP server. lanceglass has none (CLI +
  HTTP + maw plugin only), so if an Oracle is to *query* session history as
  tools, session-search is the integration point, not lanceglass.

## 7. Honest limits of this analysis

- I ran `plan` and two bounded `import` batches into a scratchpad store. I did
  **not** run a full 513-file import, so I have no number for total events in our
  history, and no measurement of how long it takes.
- I did not run the embedding path at all - no provider is configured here.
- I did not test the UI, the History workspace, or the vector map.
- The 12 sibling repos were read at README depth only, except lanceglass.

## 8. Correction: lanceglass has no semantic search

Verified 2026-09-03 after three subagents independently flagged it, then checked
myself. lanceglass **writes** embeddings and never **queries** them by similarity:

- No ANN call, no index build, no ranking, no fusion. The only `cosine` strings
  in `src/` name the distance metric inside an embedding-space identity, not a query.
- Every read of the vector store is an exact primary-key lookup
  (`src/database.vector.ts:157,182`): ``.where(`event_id IN (...)`)``.
- None of the twelve HTTP routes is a search route. `/api/vectors/visualize`
  returns a PCA scatter of already-computed vectors.
- `lessons/08-optional-embeddings.md` calls semantic search "future".

**Consequence for section 4.8.** Adopting lanceglass would give us a correct,
idempotent, provenance-preserving index of session history plus a scatter plot.
It would NOT close the semantic-search question our vec0 work was about. That
stays separate work whichever way we go, and should be decided on its own merits.

There is also no PII or secret redaction of session content: raw JSONL text is
stored and embedded unredacted. What exists is a `<system-reminder>` content
filter (embedding quality, not privacy), credential stripping in outbound
Cloudflare *error strings* only, and a loopback-only network guard. Every
request is rejected unless `Host` is loopback, and beyond that there is no auth
at all - so a running instance is co-resident-only and then wide open.
