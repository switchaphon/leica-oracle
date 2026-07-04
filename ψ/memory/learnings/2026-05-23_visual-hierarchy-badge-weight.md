# Visual Hierarchy via Badge Weight

**Date**: 2026-05-23
**Source**: SOT alignment session — StatusBadge vs ServiceTypePill redesign
**Confidence**: High (validated by user, applied across all prototype pages)

## Pattern

When two badge types coexist in the same UI row (e.g., service type + workflow status), use **fill weight** to establish hierarchy:

- **Primary identity** (what it IS): 3-tone filled — `bg-{color}-50 + text-{color}-700 + border-{color}-200` + icon
- **Secondary context** (where it IS in workflow): 2-tone outline — `bg-transparent + text-{color}-600 + border-{color}-300`, text-only

The `bg-fill` is the single strongest visual cue. Removing it creates instant subordination without changing the color palette.

## Applied In

- ServiceTypePill (3-tone + icon) = primary → tells you "ตรวจทั่วไป" / "ศัลยกรรม"
- StatusBadge (2-tone outline) = secondary → tells you "รอตรวจ" / "เสร็จสิ้น"

## Why Not Just Use Different Colors?

Both badge types already use different colors. But when both are 3-tone filled, they compete for attention at equal visual weight. The user's eye has to consciously parse which is which. With fill-weight hierarchy, the service type badge registers first (filled = solid = important), status registers second (outline = lightweight = context).

## Anti-Pattern

Using colored text without badges for status items in dropdown lists — "ลายตาไป" (too visually noisy). Colored dots + neutral text is cleaner for list scanning.
