---
date: 2026-06-11
source: "rrr: pops/vet"
tags: [css, flex, layout, popover, radix]
---

# min-w-0 overflow-hidden prevents flex layout shift from popover content

When a flex child contains a Radix Popover with `min-w-[320px]`, the popover content can push the flex child wider than its ratio allows. Once the popover closes, the parent flex container doesn't shrink the child back — the layout "drifts" permanently.

**Fix**: Add `min-w-0 overflow-hidden` to the flex child. `min-w-0` overrides the default `min-width: auto` that prevents flex items from shrinking below their content size. `overflow-hidden` clips any absolute content that might still contribute to intrinsic size calculation.

**Evidence**: OrderSummaryPane shifted from 528px → 436px (92px drift) when switching between appointments with different label lengths. After adding `min-w-0 overflow-hidden`, width stayed at 342px across all states — verified with Playwright bounding box measurements.
