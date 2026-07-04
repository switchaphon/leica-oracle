# Learnings — Diagnostic Order Origin Grill (2026-05-30)

Source: `/grill-me` design session → `DIAGNOSTIC_ORDER_ORIGIN_PRD.md`. Four reusable patterns + one process lesson.

## 1. Asymmetric friction — gate only the expensive, irreversible direction (HIGH confidence)

When a control toggles between two modes where one is cheap/reversible and the other spawns a second entity or commits a downstream cost, **put friction only on the expensive direction.**

- สั่งตรวจเพิ่ม (this visit, OPD waits) = cheap, instantly correctable → save directly, no confirm.
- สั่งตรวจล่วงหน้า (future) = creates/links an appointment, prep instructions, owner expectation → confirmation popup gating it.

Corollary: the dangerous direction is *self-gating* if its consequence is revealed in context — switching to ล่วงหน้า makes the appointment field appear, so you can't slide into it silently. neon-oracle arrived at the same "asymmetric friction" independently — cross-consult convergence is a strong signal a pattern is right.

## 2. Reuse a DS pattern for mode differentiation before inventing one (HIGH)

I first proposed a small color toggle for เพิ่ม/ล่วงหน้า. Un pointed at an existing full-width **tab selector** (the vet-schedule modal's เวรลงตรวจ/นัดหมาย tabs) → adopt that as the order-mode selector. Benefits: zero new pattern, DS-consistent, and **the active tab doubles as the modal title** (strong differentiation with no extra label). Lesson: when you need "make these two modes obviously different," scan the design system for an existing two-state container first.

## 3. A coupling field ≠ "an entity of that kind exists nearby" (MEDIUM-HIGH)

I labeled "เพิ่ม order + an appointment" as unnatural; Un corrected me. A same-visit order's `appointment_no` stays NULL even when a follow-up appointment coexists in that visit — they are **two independent objects**. Don't couple A to B just because B is present; couple only when A's lifecycle actually depends on B's. (Cancelling the follow-up must not void today's completed lab.)

## 4. The "edge case" often collapses into existing flows + one narrow gap (MEDIUM)

Q4 (add an order after the visit closed, owner phones back) looked like a new sub-system. It collapsed to: appointment creation = already multi-entry (pet profile / vet profile / appointment list / [+]); the *only* real gap = a vet-only surface to create a diagnostic order outside SOAP. Before designing an edge case, separate "what already exists" from "the one new thing."

## 5. PROCESS — read the brain's recent learnings/audits at grill start, not just the code (HIGH)

This grill designed an FE advance-order flow on top of a backend that (per a **same-day** schema-gap audit, `ψ/learn/pops/vet/2026-05-30/schema-gap-audit/02_diagnostic.md`, finding DIAG-01 CRITICAL) cannot store it: diagnostic orders require `queue_id`+`medical_record_id` NOT NULL, so an order cannot precede its receiving visit, and none of `source_visit_no`/`target_visit_no`/`appointment_no`/`wait_for_result`/`NO_SHOW` exist. The PRD is sound as a *target* spec but the gap should have been surfaced up front. **At the start of any design grill that touches persistence, grep the brain's recent `ψ/learn/**` audits + `ψ/memory/learnings/` for the same entity.** Connects to `2026-05-23_check-be-spec-before-ui-taxonomy.md` and `2026-05-22_service-type-is-not-lifecycle.md`.

## 6. PROCESS — match the user's interaction mode (MEDIUM)

Un grills in prose and rejected AskUserQuestion twice ("clarify first"). After one rejection, drop the structured-pick tool and stay conversational. Also: write Thai natively, not literal-translated (see feedback memory `feedback_natural_thai_writing`).
