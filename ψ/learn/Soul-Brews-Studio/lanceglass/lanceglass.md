# lanceglass Learning Index

## Source
- **Origin**: ./origin/  (symlink to `$GHQ_ROOT/github.com/Soul-Brews-Studio/lanceglass`)
- **GitHub**: https://github.com/Soul-Brews-Studio/lanceglass
- **Version read**: 26.9.1-alpha.1401 | MIT | Bun + LanceDB 0.27.2

> A local-first looking glass for Claude Code and Codex JSONL histories.
> Turns append-only agent session logs into a typed, inspectable LanceDB.

## Explorations

### 2026-09-03 1130 (--deep, 5 agents)
- [[2026-09-03/1130_ARCHITECTURE|Architecture]] - structure, entry points, the three-table schema, data flow
- [[2026-09-03/1130_CODE-SNIPPETS|Code Snippets]] - normalizer, identity derivation, import, embed, search, verbatim
- [[2026-09-03/1130_QUICK-REFERENCE|Quick Reference]] - operator's manual, every CLI flag, all 8 lessons summarised
- [[2026-09-03/1130_TESTING|Testing]] - proof discipline, the smoke gate, determinism without a live model
- [[2026-09-03/1130_API-SURFACE|API Surface]] - HTTP endpoints, the maw plugin contract, extension points

**Key insights**

1. **Two physical stores, not one.** `.data/lancedb` (events, event_sources,
   source_files) and `.data/lancedb.vector[.<space>]` (event_vectors). Import
   never contacts an embedding service. Embeddings are derived data, rebuildable
   from the plain store, and each incompatible model revision gets its OWN
   physical store - "The Spaces Never Blur Rule".

2. **Three identities, not one.** Canonical event id is content-derived
   (`${event_uuid}#${block_index}`); a separate `event_sources` row records each
   *observation* (file, line, hash); `source_files` is the manifest. The event
   survives a file move. Our `oracle_documents` collapses all three into one
   derived `source_file` string - see
   [[../../../memory/learnings/2026-09-03_our-memory-index-points-at-derived-paths]].

3. **Resume is a hash comparison, not a cursor.** Embedding skips rows whose
   `text_hash + model + dimension` are already current, so a failed batch costs
   only the failed batch. The importer snapshots the exact byte length seen at
   preflight and parses only that immutable prefix, so a live-appending JSONL
   file cannot corrupt a run - the new bytes are simply a "changed" file next pass.

4. **Progress on stderr, the report on stdout.** A long LanceDB merge never looks
   frozen, and `| jq` stays safe. Cheap to copy, immediately useful.

5. **The named rules are the real artifact.** DESIGN.md carries a dozen of them.
   The ones that transfer beyond UI: *The CLI Is the Evidence Rule* (the browser
   never invents progress, it shows the same process output), *The Visible Window
   Rule* (charts summarise only the returned window and must say so), *The
   Calendar Is Evidence Rule* (zero-work days stay visible; absence is a finding).

**Verified on this machine, 2026-09-03**
- `bun src/cli.ts plan --source claude` -> `found: 513` - it sees every tier of
  our corpus, including the 254 files a `<project>/*.jsonl` glob misses. Wrote nothing.
- Bounded import of 3 real files -> 292 records, 132 blocks, 0 corrupt.
- Re-running the identical command reported `unchanged: 3` and advanced to the
  next batch. 498 events, 0 duplicates. Idempotency holds.
- `maw-plugin/index.ts:187` has the `import.meta.main` guard, so it does NOT
  silently no-op under maw-rs. See [[maw_rs_plugin_shim]].
