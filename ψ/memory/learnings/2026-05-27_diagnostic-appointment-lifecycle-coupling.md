# Lesson: Diagnostic Order Needs Appointment Lifecycle Coupling

**Date**: 2026-05-27
**Source**: Grill session on diagnostic-flow.html Section 4
**Confidence**: High (Un confirmed the separation of concerns)

## Pattern

When a domain entity (diagnostic order) references another entity's ID for **data routing** (which SOAP note to attach results to), that does NOT solve **lifecycle coupling** (what happens when a linked appointment changes state). These are separate concerns requiring separate fields.

## Concrete Application in POPs

| Field | Purpose | When it matters |
|-------|---------|----------------|
| `source_visit_no` | Which OPD created the order | Always — traces origin |
| `target_visit_no` | Which OPD receives the result | Result attachment (COMPLETED → SOAP) |
| `appointment_no` (NEW) | Which appointment the pet is expected to arrive on | Cascade: APT CANCELLED/NO_SHOW/RESCHEDULED → mark diagnostic order accordingly |

Without `appointment_no`, "สั่งตรวจล่วงหน้า" orders with `target_visit_no = NULL` become orphans when the pet never shows up — PENDING forever in the lab queue.

## Design Constraints Identified

1. `appointment_no` should be NOT NULL for "สั่งตรวจล่วงหน้า" (Case B must not exist)
2. `appointment_no` should be NULL for "สั่งตรวจเพิ่ม" (same-visit, no appointment link needed)
3. Edge case: vet adds diagnostic order after appointment already booked → blocked by `source_opd_id NOT NULL` — needs resolution

## Unresolved

- Cascade behavior per appointment state (CANCELLED → ?, RESCHEDULED → ?, NO_SHOW → ?)
- Whether diagnostic order needs new states or reuses CANCELLED
- Reception check-in UX for surfacing pending diagnostic orders

## Broader Pattern

This routing-vs-lifecycle separation likely applies anywhere POPs links entities across time boundaries (e.g., prescription refill orders linked to follow-up appointments, vaccination schedules linked to booster appointments).
