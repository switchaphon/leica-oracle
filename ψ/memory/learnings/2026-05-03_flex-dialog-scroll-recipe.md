# Flex Dialog Scroll Recipe + Production-First Rule

**Date**: 2026-05-03
**Source**: rrr --deep: pops-clinic-oracle
**Confidence**: High (validated through 4 failures and 1 working solution)

## Pattern 1: Flex Column Scroll in Dialog/Modal

The canonical recipe for a scrollable middle section in a flex-column Dialog:

```
Dialog (flex flex-col, max-h-[88vh])
  Header (shrink-0)
  Scroll area (min-h-0 flex-1 overflow-y-auto)     <- KEY: min-h-0
    Inner wrapper (space-y-3 px-5 pb-4 pt-4)        <- padding HERE
      ...content...
    Sticky gradient (sticky bottom-0 h-8 from-white) <- flush with footer
  Footer (shrink-0 border-t)
```

**Why `min-h-0`**: Flex children default to `min-height: auto`, meaning they grow to fit content and never shrink. `min-h-0` allows the flex item to shrink below content height, enabling overflow scroll.

**Why padding on inner wrapper**: Padding on the scroll container creates a gap between sticky elements and the container edge. Inner wrapper keeps the sticky gradient flush with the footer border.

### What fails:
- `h-full` on scroll child inside relative wrapper -> doesn't constrain, no scroll
- `absolute inset-0` on scroll child -> removed from flow, parent collapses to zero
- `overflow-hidden` on parent wrapper -> clips without enabling child scroll

## Pattern 2: Production-First Rule

Before building any new modal/drawer/dialog:
1. Search production code for existing implementations: `grep -ril "modal\|drawer\|dialog" src/app/_components/`
2. Read the closest match fully — props, steps, footer buttons, state management
3. Adopt patterns: step naming, button labels, color semantics, layout structure
4. Only diverge where the prototype deliberately explores something new

**Why**: Production AddLabOrderModal already had the exact 2-step flow, Collapsible categories, 3 footer buttons, and note maxLength=50 that we reinvented from scratch.

## Pattern 3: Diagnose Layout Model Before Writing CSS

When a layout breaks:
1. Identify the layout context (flex, grid, block)
2. Check default values (min-height, flex-basis, overflow)
3. Write one targeted fix
4. Do NOT trial-and-error multiple CSS changes — each creates a new regression

## Tags
`css` `flex` `scroll` `dialog` `modal` `layout` `min-h-0` `production-first` `regression-prevention`
