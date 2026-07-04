# Sidebar Flex Height Matching + DS Palette Discipline

**Date**: 2026-05-27
**Context**: Appointment page sidebar overflowed past table height; heatmap used wrong colors
**Confidence**: High (verified in browser, corrected by user)

## Pattern 1: Fill-remaining-height scroll container in flex

When a sidebar card must fill the remaining vertical space inside a flex column:

```
Parent:       items-stretch           (both columns = same height)
Sidebar:      flex flex-col gap-4     (vertical stack)
Fixed cards:  (no special class)      (calendar, workload — natural height)
Fill card:    flex-1 min-h-0 flex flex-col
  CardContent:  flex-1 min-h-0 flex flex-col
    Header:     shrink-0
    Scroll:     relative flex-1 min-h-0
      Inner:    absolute inset-0 overflow-y-auto [scrollbar-width:none]
      Fade:     absolute bottom-0 bg-gradient-to-t from-white
```

Key: `min-h-0` on every flex ancestor — without it, flex children won't shrink below content size.

## Pattern 2: Gradient heatmap with backgroundSize

```css
background-image: linear-gradient(to right, green, yellow, orange, red);
background-size: ${(maxScale / count) * 100}% 100%;
```

This stretches the full gradient across the theoretical maximum. A 50% bar reveals green→yellow; 100% reveals the full sweep. Always use DS semantic tokens for the color stops (Success → Warning → brand-orange → Error).

## Pattern 3: DS palette before any new color

Never reach for HSL/RGB interpolation. Check the design system's semantic colors first:
- Success: #16A34A
- Warning: #CA8A04
- Orange: #F07A00
- Error: #B91C1C

These are the only green/yellow/orange/red allowed in prototypes.

## Pattern 4: Optional field + fallback for incremental mock data

Adding `date?: string` with runtime fallback `a.date || TODAY` lets you add multi-day data without editing existing entries. Useful when mock arrays are 200+ lines.
