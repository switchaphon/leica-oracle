---
title: "Draft → Verify → Deploy: never ship knowledge without PM verification"
date: 2026-06-16
source: "rrr: codex fleet deployment — 8 wrong paths caught by PM Oracle"
confidence: high
tags: [workflow, delegation, verification, knowledge-drift]
---

## Pattern

When Leica generates project-specific content (AGENTS.md, agent configs, briefs):

1. **Draft** — Leica writes from CLAUDE.md + deep-learn snapshots
2. **Verify** — PM Oracle checks against actual codebase (file paths, versions, patterns)
3. **Deploy** — only after PM confirms accuracy

## Why

CLAUDE.md and deep-learn snapshots go stale. Paths get renamed, versions bump, patterns evolve. Leica doesn't live in the project — PM Oracle does.

## Evidence (2026-06-15)

Leica deployed AGENTS.md to pops/vet with 8 errors:
- Next.js 16 → actually 15
- `src/app/_utils/graphql-operations.ts` → actually `src/app/_assets/lib/graphql-operations.ts`
- Test files colocated → actually `src/__tests__/`
- 5 more path errors

PM Oracle found and fixed all 8 in one review pass.

## Also applies to

- Fleet teaching: Leica drafts the lesson, but each oracle should internalize + adapt (not just copy)
- Nat's recipe vs our setup: should have asked "who solved this?" before building from scratch
