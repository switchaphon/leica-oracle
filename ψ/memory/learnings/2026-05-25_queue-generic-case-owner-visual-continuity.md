# Lesson: Queue genericity + visual color continuity in flow docs

**Date**: 2026-05-25
**Source**: /grill-me session on queue-flow + opd-flow Target architecture
**Repo**: pops/vet

## Patterns

1. **Queue "case owner" abstraction** — Queue doesn't need to know if the actor is a vet or grooming staff. The concept of "เจ้าของเคส" (case owner) resolves per service_type at the service entity level. This keeps the Queue state machine identical for all service types. Adding a new service type (e.g., boarding) requires zero Queue changes — only a new service entity with its own lifecycle.

2. **Visual color continuity across doc sections** — When entities are color-coded in one section (e.g., Connection cards with blue/purple/green/yellow borders), every subsequent section that references those entities must use the same colors. Readers scan colors before reading text. All-purple highlights in SOAP for items that create different entities breaks the visual mapping.

3. **Diagnostic block placement is CTA-dependent** — "สั่งตรวจเพิ่ม" (from Objective) → block in Objective, wait=true. "สั่งตรวจล่วงหน้า" (from Plan) → block in Plan, wait=false. Slash commands (/lab /xray /us) default by section but show a popup to let the user toggle. Don't document it as "always in Objective."

4. **Separate downstream transitions from side entities** — In a Connection diagram, downstream (Queue WAITING_PAYMENT) is a lifecycle transition. Side entities (Diagnostic, Prescription, Appointment) are created during the lifecycle. Mixing them in one column confuses the reader about directionality.

## Anti-patterns

- Committing one fix at a time instead of planning a full edit pass after a grill session
- Using absolute paths (`/prototype/docs/...`) in HTML docs that may be viewed via file:// protocol
- Leaving `.highlight` CSS class as one color when highlighted items represent different entity types
