---
name: trace-prop-origins
description: When removing component behavior, trace where the prop comes from — parent hooks may still drive the old behavior
metadata:
  type: feedback
---

Removing auto-select from AppointmentChip was useless because `useOrderMode.ts` was setting `selectedAppointment` to the AUTO_LINKED appointment on mount. The component was a pure display — the behavior lived in the hook.

**Why:** Un saw the dropdown still auto-selected even after I "fixed" the chip. The prop `selected` was already set before the chip rendered.

**How to apply:** When changing behavior (not just display), grep for where the state/prop is SET, not just where it's RENDERED. Fix the source (hook/parent), not the leaf (component).

Related: [[grep-before-edit]]
