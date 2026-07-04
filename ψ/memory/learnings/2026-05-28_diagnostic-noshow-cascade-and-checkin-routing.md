# Lesson: Diagnostic Order NO_SHOW State + Check-in Routing

**Date**: 2026-05-28
**Source**: Grill session continuation on diagnostic-flow.html

## Pattern: Mirror state names across coupled entities

When two entities are lifecycle-coupled (Diagnostic Order ↔ Appointment), use the SAME state names for cascaded states. Don't invent new names like SUSPENDED — use NO_SHOW so staff understands instantly that it came from an appointment NO_SHOW.

## Cascade Rules Decided

- CANCELLED → order CANCELLED (if DRAFT/PENDING), flag if IN_PROGRESS+
- RESCHEDULED → re-link appointment_no to new appointment (no state change)
- NO_SHOW → order NO_SHOW (not terminal — staff decides: re-link or cancel)

## Check-in Routing

Advance diagnostic orders → pet goes to Lab/X-ray BEFORE exam room. Vet already decided — no need to confirm again. Saves time: by the time pet sees vet, results are ready.

## Data Model Final

- `source_visit_no`: nullable (nice-to-have SOAP link)
- `target_visit_no`: nullable (auto-attach)
- `appointment_no`: nullable (NULL for same-visit, NOT NULL for advance)
- `ordered_by_staff_id`: NOT NULL (always present, already existed)
