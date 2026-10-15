# Soul-Brews-Studio: the memory constellation (surveyed 2026-09-03)

> Question asked: "is there another repo in Soul-Brews-Studio I need to know about
> besides lanceglass?" Answer: yes. lanceglass is one node in a cluster of ~10
> memory repos Nat published between 2026-08-29 and 2026-09-02.

## How I surveyed

`gh repo list Soul-Brews-Studio --limit 200` returned 118 repos. I sorted by
`pushedAt`, then fetched the README of every repo whose description mentioned
memory, session, JSONL, vault, or Lance. Creation dates came from
`gh api repos/Soul-Brews-Studio/<r> --jq .created_at`.

Every repo below is public, MIT, and squashed to a single commit - these are
public releases of private work, not the working history.

## The cluster

| Repo | Created | Lang | What it is |
|---|---|---|---|
| **lanceglass** | 2026-09-01 | TS | Claude Code + Codex JSONL -> LanceDB. Plain store and vector store physically separated. The one we deep-learned. |
| **lance-indexer** | 2026-09-01 | TS | Sibling of lanceglass: block-level search, provenance drill-down, RAG evidence, pluggable vector map. Three tables (events/files/vectors). |
| **memory-horizon** | 2026-09-01 | TS | Reads the same JSONL as short/mid/long-term memory and classifies it: LIVE, COOLING, DORMANT, STALE, DEPRECATED, LOST. Explicitly NOT a vector database. |
| **session-viewer** | 2026-09-01 | Swift | Native indexer/reader for CC transcripts across parent, subagent and workflow-agent tiers. Owns the SQLite index. |
| **session-search** | 2026-09-01 | TS | Read-only CLI + MCP over session-viewer's index. FTS5 unicode61 for short queries, trigram for Thai substring search. |
| **psi-memory-open** | 2026-08-29 | Swift | Local-first read-only macOS atlas over **psi vaults** - our exact brain directory shape. Metadata inventory, redacted markdown index, RealityKit "Brain Universe". |
| **psi-memory-lab** | 2026-09-01 | Swift | Same product, lab distribution. |
| **arra-memory-lab** | 2026-09-01 | TS | Cloudflare D1 + Workers AI. Teaches the *contracts*: authority tiers, honest recall, evidence lineage, dry-run-first mutation. |
| **memory-lab-2sep** | 2026-09-02 | TS | Memory MCP on Workers + D1 with a ledger of who called what from where. Built for a workshop. |
| **higher-order-mcp** | 2026-09-02 | TS | Renameable OAuth MCP template whose tools can create tools at runtime. |
| **arra-memory-haos** | 2026-08-30 | TS | The same memory corpus as a Home Assistant add-on, embedded libSQL. |
| **hook-lance** | 2026-09-02 | TS | Webhooks -> LanceDB -> Discord/HTTP rules. Ingest, not memory-core. |

## The division of labour that matters to us

Three of these read *different halves of our data*:

```
  our 513 JSONL session files (484 MB)   ->  lanceglass / lance-indexer / session-viewer
  our 688 psi markdown files  (369 MB)   ->  psi-memory-open
  classification over either corpus      ->  memory-horizon
  the contracts a memory API should obey ->  arra-memory-lab
```

`arra-oracle-v3` - the MCP we actually run - sits in none of these lanes. It
indexes 258 hand-written learning documents and nothing else.

## The one repo I would read next

**memory-horizon**, because its six-state classification (LIVE / COOLING /
DORMANT / STALE / DEPRECATED / LOST) is the vocabulary for a problem we can
already measure: 224 of our 258 indexed documents are LOST by its definition -
previously observed evidence no longer present at the recorded location.

Second: **psi-memory-open**, because it is the only tool in the family built for
the markdown vault shape our memory actually uses.
