---
name: grep-before-edit
description: When changing a UI pattern, grep for ALL files rendering that pattern and change them atomically — never fix one file and forget siblings
metadata:
  type: feedback
---

When Un gives a UI change (e.g. "เปลี่ยน นัดปลายทาง เป็น วันนัด"), the same pattern often lives in multiple files (AppointmentChip.tsx for OPD, DiagnosticRequestList.tsx for diagnostic list, step badges in 4 page files). Changing one and missing others causes repeated "ทำไมยังไม่เห็นแก้" cycles.

**Why:** Un expects consistency across all flows. A partial change is worse than no change — it creates visible inconsistency.

**How to apply:** Before the first edit, `grep -rn "old-pattern"` across the prototype directory. List every file. Change them all in one pass. Verify each flow in browser.

Related: [[ds-is-literal]], [[trace-prop-origins]]
