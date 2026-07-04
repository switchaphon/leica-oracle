# Cross-Product Design System Derivation Pattern

**Date**: 2026-05-03
**Context**: Creating pops-clinic design system from pawrent's established tokens
**Confidence**: HIGH (validated this session, reinforces prior learnings)

## The Pattern

When creating a design system for product B that shares brand DNA with product A:

1. **Read product A's tokens first** — gives concrete decisions to diverge FROM
2. **Spawn brand (Pixel) + UI (Neon) specialists in parallel** — two opinionated proposals are better than one
3. **Include user feedback BEFORE synthesis** — course-correct at token level, not page level
4. **Ground specialist briefs in codebase reality** — what's already loaded (fonts, colors in tailwind.config) constrains the design space
5. **Document "Fun Injection Points" explicitly** — map WHERE personality belongs so future builders don't default to boring OR chaotic
6. **Finalize the spec document BEFORE spawning builders** — enables zero-coordination parallelism

## The Formula for "Professional But Fun"

```
DATA ZONES = calm (white bg, neutral text, no brand color)
BRAND ZONES = personality (gradient, pink, shimmer, colorful chips)
INTERACTION = subtle brand peek (pink hover, focus ring)
```

Specific fun injection points that work:
- Queue status as color rainbow (practical AND joyful)
- Pink shimmer on loading skeletons (brand during dead time)
- POPS gradient in sidebar header (brand heartbeat on every screen)
- Colorful category icons (each type has identity)
- Table row hover in brand-tint (brand on every interaction)

## Anti-Patterns

- Don't use brand colors for semantic signals (pink ≠ error in medical tools)
- Don't add gradient to data surfaces (kills readability)
- Don't copy sibling product's radius/warmth (they serve different emotions)
- Don't brief specialists without including what the codebase already has

## Connects To

- `2026-04-29_read-sibling-prototypes-first.md` — same principle at component level
- `feedback_reuse_components.md` — always check what exists before creating new
- `2026-04-29_cross-session-file-ownership.md` — parallelism requires isolation
