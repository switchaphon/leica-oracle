---
name: alignment-work-cascades
description: Aligning one page to a reference convention reliably cascades into full lifecycle/KPI/doc redesign — budget for it
metadata:
  type: feedback
---

When asked to "compare X page with Y reference" or "align to convention", the work always cascades beyond the original surface.

**Evidence (3 instances):**
- 2026-05-04: Dashboard rebuild — "make it look like Figma" → 3 layout passes, 70/30 split, new component patterns
- 2026-05-23: SOT alignment — "fix 3 hex values" → touched 16 files, 7.5-hour session
- 2026-05-27: Appointment alignment — "compare table with dashboard" → removed COMPLETED state, added RESCHEDULED, redesigned KPI cards 5→3, updated flow docs, designed sidebar

**Why:** Alignment is a probe. Comparing surface A with reference B reveals accumulated drift in the entire page — not just the element being compared. Once you fix the table columns, the data model inconsistency becomes visible. Once you fix the data model, the KPI cards are wrong. Each fix exposes the next layer.

**How to apply:**
- When Un asks to align/compare, proactively flag: "this will likely cascade — scope to surface-only, or audit the full page?"
- Budget 2-4x the estimated time
- Treat alignment as an audit, not formatting — use [[table-convention-propagation]] pattern
- Always check flow docs before touching state models
