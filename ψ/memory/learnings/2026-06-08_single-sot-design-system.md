# Lesson: Single Source of Truth for Design Systems

**Date**: 2026-06-08
**Context**: Design system had 3 files (DESIGN_SYSTEM.md, DESIGN.md, DS_MARKDOWN in page.tsx) — all drifting with 14 conflicts over 5 weeks
**Repo**: pops/vet

## Pattern

Design token documentation must live where it's consumed. A static markdown file that requires manual re-export will always drift from the live implementation.

Three files = three truths = zero trust. When a developer reads conflicting card radius values (8px vs 16px) or different warning hex codes (#D97706 vs #CA8A04), they pick whichever they saw first — which may be the wrong one.

## Resolution

Consolidated to one constant (`DS_MARKDOWN` in `design-system/page.tsx`) that:
- Powers the live interactive design system page
- Feeds View/Download .md and .html exports on demand
- Cannot drift from itself

Merged the deep-doc's unique value (philosophy, accessibility, CSS vars) into the live constant. Deleted the static files.

## Tags

design-system, documentation-drift, single-source-of-truth, gap-audit
