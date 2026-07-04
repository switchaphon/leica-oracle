# Lesson: Process Accumulation Signals Architecture Debt

**Date**: 2026-06-08
**Context**: 5 weeks of adding checklists to maintain 3 design system files, culminating in 14 silent conflicts
**Confidence**: HIGH — observed the full arc from first checklist to consolidation

## Pattern

When you keep adding process rules ("always sync X", "never skip Y", "post-commit checklist Z") to maintain consistency between artifacts, the real problem is having multiple artifacts. Each rule is a band-aid on an architectural problem: multiple sources of truth.

## Evidence (pops/vet design system)

| Date | Rule Added | What it compensated for |
|------|-----------|----------------------|
| 2026-05-04 | "DS is source of truth" | Two docs existed; needed to declare a winner |
| 2026-05-18 | "Re-export DESIGN.md after every commit" | Static file kept falling behind live page |
| 2026-05-18 | "Never skip post-commit" | Developers skipping the export step |
| 2026-06-03 | "DS page is tiebreaker" | Three docs now conflicting; needed arbitration |
| 2026-06-05 | "Check DS compliance before shipping" | Unclear which doc's values to check against |

By June 8: 14 conflicts had accumulated silently despite all 5 process rules being in place.

## Resolution

Delete the extra artifacts. Consolidate to one living constant that powers the live page + exports. Zero sync steps = zero drift.

## Generalizable insight

Count your "maintenance rules" for a given artifact family. If the count exceeds 2, you probably have an architecture problem wearing a process hat.

## Tags

architecture, process-debt, single-source-of-truth, documentation-drift, design-system
