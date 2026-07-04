---
date: 2026-06-11
session: diagnostic-modal-cleanup
trigger: advance order producing PENDING instead of PLANNED
---

# Spec state machine must match buildOrder, not just display layer

When a spec doc (e.g. diagnostic-flow.html) defines a lifecycle like DRAFT→PLANNED→PENDING, it's not enough for the display layer (badges, chips, lists) to support all states. The data-producing function (`buildOrder`) must emit the correct status at creation time.

In this case, DiagnosticOrderList, diagnostic-block, and SOAPContent all had PLANNED styling wired up from earlier grill sessions — but all three selectors hardcoded `buildOrder('PENDING')` for both immediate and advance orders. The gap was invisible until Un cross-referenced the live prototype against the spec doc.

**Pattern**: after any state machine grill/decision, grep for the status-producing code (not just the status-displaying code) and verify alignment.
