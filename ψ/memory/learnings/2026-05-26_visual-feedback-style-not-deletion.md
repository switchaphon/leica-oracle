# Visual Feedback Means Style Change, Not Deletion

**Date**: 2026-05-26
**Source**: rrr --deep: pops-clinic-oracle (session part 2)
**Confidence**: High (burned by git checkout + redo cycle)

## Pattern

When a user gives visual feedback like "ไม่เอา X" or "ไม่ต้องมี X" about a diagram element, the default interpretation should be **change X's appearance**, not **delete X**. Only remove elements when explicitly confirmed.

## Evidence

Un said "ไม่เอาเส้นโค้ง" about curved arcs overlapping boxes. I commented out the cancel paths + skip paths entirely. Un corrected: "ไม่ได้ให้ซ่อน แค่เปลี่ยนจากเส้นโค้งเป็นหักมุม" — just change curves to polylines. Had to git checkout and redo.

## Reusable Techniques

1. **SVG agent briefs: specify path type** — "polyline only, no bezier C/Q commands" prevents curve→overlap issues
2. **Position from container, not content** — `text-anchor="end"` at lane edge, not x-offset from sibling text width
3. **CHANGELOG maintenance** — update prototype CHANGELOG constant every session, not just repo CHANGELOG.md

## Tags

visual-feedback, svg, polyline, agent-brief, changelog-maintenance
