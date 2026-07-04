---
date: 2026-05-17
source: "rrr: pops/vet"
concepts: [design-system, button-states, accessibility, semantics]
---

# Disabled buttons keep their variant's visual identity

A disabled button should retain the visual style of its variant — `solid NEUTRAL + disabled`, not `outline + disabled`. The variant communicates WHO the action is for (my role vs other role). The disabled state communicates WHETHER I can act. Mixing the two (outline for a same-role disabled action) sends a conflicting signal: "this is another role's action" when it's actually "your action, but you lack permission for this specific case."

Context: Queue table "เรียกเข้าห้องตรวจ" button was rendering as outline+disabled for non-owner vets. Should be solid NEUTRAL+disabled — the action belongs to the vet role, just not this specific vet.
