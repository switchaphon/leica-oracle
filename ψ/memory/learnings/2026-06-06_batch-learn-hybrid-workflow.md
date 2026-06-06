# Batch /learn Hybrid Workflow

**Date**: 2026-06-06
**Source**: rrr --deep, leica-oracle
**Confidence**: High (proven in session)

## Pattern

When batch-learning mixed URL types (repos + gists + articles), use a hybrid approach:
- **Full agents** (3 Haiku) for actual code repos — they need exploration
- **Direct download** (curl + API) for gists and articles — they're already documentation, no exploration needed
- **Hub-first indexing** — create a hub .md file per source that links to all docs, with 1-line key insights

## Evidence

Session 2026-06-06: 15 URLs processed in ~10 minutes
- 1 GitHub repo (marckrenn/claude-code-changelog) → 3 agents → 3 docs
- 14 gists → direct curl from GitHub API → 20 files
- 3 hub files created as navigation entry points

## Key Sub-Patterns

### Gist Organization
```
ψ/learn/{owner}/gists/
├── gists.md          # Hub file — index with key insights
└── YYYY-MM-DD/
    └── HHMM_{slug}.md  # Time-prefixed content files
```

### Hub-First Entry
1. Create index file with title + source + 1-liner per doc
2. Batch-fetch all sources in parallel
3. Scan hubs for quick context before deep-reading
4. Drill into 2-3 critical items only

Saves 60-70% read time vs sequential deep dives.

### Topology Mapping (from Nat's gists)
For any multi-system comparison, ask per system:
- What question does it answer?
- Who holds state?
- Where does it collide with others?
- Where does it complement?
- What's the sweet spot for combining?

## Connections

- Relates to: maw CLI patterns, hermes MCP pivot, fleet coordination
- Applies to: any future /learn batch session, especially mixed URL types
- Gap: /learn skill needs native `--gist` mode and batch URL tracking
