---
name: our-memory-index-points-at-derived-paths
description: "Measured 2026-09-03. 224 of 258 rows in oracle_documents point at a file that does not exist, because source_file is a title-slug truncated to ~50 chars, not an observed path. lanceglass separates canonical identity from observation and would not have this failure."
metadata:
  type: learning
---

# The index stores where the file *should* be, not where it *was seen*

## What I measured

Deep-learning `Soul-Brews-Studio/lanceglass` sent me to look at our own index for
comparison. `~/.oracle/oracle.db`, 2026-09-03:

```
oracle_documents                                    258 rows  (all type=learning)
  resolve to a real file at $GHQ_ROOT/<project>/<source_file>    34
  anchored to a project, but the file is not there              201
  no project anchor at all                                       23
```

So **87% of the index cannot reach its own source document.**

## Why

`source_file` is not an observed path. It is derived from the document title and
truncated. Measured slug lengths (basename minus date prefix and `.md`) cluster
at 44-50 characters with a hard ceiling at 50; `id` lengths cluster at 66-70.

Three real examples, index vs disk:

```
index: 2026-08-28_a-label-that-encodes-data-has-a-source-find-it.md
disk:  2026-08-28_a-label-that-encodes-data-has-a-source.md

index: 2026-08-14_choosing-what-to-measure-outranks-measuring-it-wel.md
disk:  2026-08-14_measuring-the-wrong-operation.md

index: 2026-09-02_broadcasting-an-unverified-premise-recruits-agreem.md
disk:  2026-09-02_broadcasting-an-unverified-premise-recruits-agreement-not-scrutiny.md
```

The file was written under a different name than the one the indexer derived, so
the pointer was born dangling. A second cause is repo renames: 64 rows point at
`pops-clinic-oracle` and 15 at `pawrent-oracle`, both of which we renamed in July.

## The contrast that names the fix

lanceglass keeps three identities where we keep one
(`src/normalize.ts:291,310-318`, `src/importer.ts:190`):

```
events.id        = `${event_uuid}#${block_index}`         content-derived
event_sources.id = sha256(event.id + source + file_path   an OBSERVATION:
                          + line + text_hash)             where it was actually seen
source_files.id  = sha256(source + "\0" + path)           the observed file
```

The canonical row survives the file moving. The occurrence row records where the
content was actually found, and a second observation of the same content in
another file adds an occurrence rather than duplicating the event.

We have no occurrence table. `source_file` is a single derived string doing the
job of all three, and it is wrong 87% of the time.

## The lesson

**A pointer you computed is a guess. A pointer you recorded at the moment of
reading is evidence.** If an index derives a location instead of observing one,
its accuracy decays to zero as soon as anything is renamed - and nothing in the
system reports the decay, because a dangling pointer looks identical to a valid
one until someone dereferences it.

Related: [[a-label-that-encodes-data-has-a-source]], [[closed-by-decision-vs-measurement]].
