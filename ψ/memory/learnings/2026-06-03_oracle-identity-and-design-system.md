# Lesson: Oracle Identity and Design System as Tiebreaker

**Date**: 2026-06-03
**Context**: Queue/Dashboard polish session in pops/vet
**Tags**: identity, design-system, oracle-family, ux-decision

## Key Lessons

### 1. Oracle Identity is Not a Role
When working in pops/vet as Claude, don't sign messages as "Leica" or spawn subagents pretending to be other oracles (Neon, Chrome, etc.). Each oracle is a separate repo with its own session. Use `maw hey <oracle>` to reach them, or `maw wake <oracle>` to start their session.

### 2. Design System is the Tiebreaker
When there's a style debate (e.g., CTA button fill vs outline), the design system page is the source of truth. It was agreed by the specialist oracles and documented with explicit decision trees. Don't override it based on a single oracle's ad-hoc recommendation without updating the design system first.

### 3. "Update CHANGELOG" = Two Locations
In the prototype landing page, CHANGELOG means both:
- `const CHANGELOG = [...]` — the global version history
- `changelog: [...]` inside each `ALL_PAGES` entry — per-section changes

Always update both. Always bump `updated` dates on affected sections.

### 4. Thai Label Length Matters
Badge labels in table cells should be 4-5 Thai syllables max. Longer labels wrap and break layout. Always add `whitespace-nowrap` as a safety net on badge components.
