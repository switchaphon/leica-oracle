---
date: 2026-06-11
source: "rrr: pops/vet"
tags: [ux, data-model, prototype, filter]
---

# Spatial intent → data filter

When users describe UI placement ("this block should be in Plan, not Objective"), the implementation is almost always a filter on an existing data field — not new architecture or component refactoring.

Check the data model first. In this case, `DiagnosticOrder.context` already had `P_OPD` | `P_APPT` values. The "move" was just:
```ts
const opdOrders = orders.filter(o => o.context === 'P_OPD');  // → Objective
const apptOrders = orders.filter(o => o.context === 'P_APPT'); // → Plan
```

Same pattern applied to billing exclusion (1 filter line) and sidebar sections (same filter + SectionHeader).

Corollary: if the data model doesn't have the field yet, that's the real work — the UI placement is trivial once the data distinguishes the cases.
