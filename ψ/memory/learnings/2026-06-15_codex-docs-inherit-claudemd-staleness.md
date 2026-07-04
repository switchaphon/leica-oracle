# Codex Agent Docs Inherit CLAUDE.md Staleness

**Date**: 2026-06-15
**Source**: Codex agents review session
**Tags**: codex, documentation, drift, paths

## Pattern

When Leica (or any orchestrator) generates Codex agent docs (AGENTS.md, agents/*.md) from CLAUDE.md, they inherit every stale path and outdated version number in CLAUDE.md. The knowledge descriptions (auth model, RBAC, SWR patterns) stay accurate longer than filesystem paths.

## Evidence

8 issues found in freshly deployed Codex files — all were path/version mismatches:
- `graphql-operations.ts` moved from `_utils/` to `_assets/lib/`
- `authOptions.ts` moved up one directory
- Route group renamed to `(routes)` from `(protected)`
- Next.js version still listed as 16 (actually 15)
- SWR keys documented as centralized file (actually hook-local exports)

Zero conceptual errors. All architecture descriptions were correct.

## Lesson

Paths drift faster than concepts. When reviewing or generating agent docs:
1. Always verify file paths with `find`/`ls` against live codebase
2. Fix CLAUDE.md first (source of truth), then regenerate downstream docs
3. Concepts (auth model, patterns, constraints) are stable; filesystem map is volatile
