# Lesson: Three-Field Reference Pattern + Mirror State Names

**Date**: 2026-05-28
**Source**: Deep grill session on diagnostic order x appointment lifecycle
**Confidence**: High (all decisions confirmed by Un through grill)

## Pattern 1: Three-Field Reference

When Entity A references Entity B across time boundaries, you often need THREE separate fields, not one:

| Field | Purpose | Nullable? |
|-------|---------|-----------|
| `source_*` | Origin trace — where did this come from | Yes (may not always have a source context) |
| `target_*` | Result routing — where does the output go | Yes (may not know yet, auto-attach later) |
| `lifecycle_*` | Cascade trigger — when linked entity changes state, what happens | Yes (only for cross-time references) |

Concrete in POPs: `source_visit_no` (SOAP origin) + `target_visit_no` (result attachment + billing) + `appointment_no` (cascade on CANCELLED/NO_SHOW/RESCHEDULED)

## Pattern 2: Mirror State Names

When Entity A cascades state to Entity B, use THE SAME state name:
- Appointment NO_SHOW → Diagnostic Order NO_SHOW (not SUSPENDED)
- Appointment CANCELLED → Diagnostic Order CANCELLED (not VOID)

Why: staff already learned the term from the source entity. Zero cognitive load. No training debt.

Anti-pattern: inventing SUSPENDED, ON_HOLD, BLOCKED — these require explanation and create confusion about which source event triggered them.

## Pattern 3: State-Dependent Cascade

Not all states cascade equally:
- **DRAFT/PENDING** (work not started) → auto-cascade is safe
- **IN_PROGRESS+** (work started or completed) → flag for human review, never auto-cancel

Why: sunk cost is real. Lab already processed the sample → you can't un-process it.

## Broader Applicability

These patterns apply to any entity that references another across time:
- Prescription refill → follow-up appointment
- Vaccination schedule → booster appointment
- Referral letter → receiving clinic's visit
