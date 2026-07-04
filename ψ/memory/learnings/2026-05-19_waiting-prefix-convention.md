# WAITING_* Naming Convention for Queue Statuses

**Date**: 2026-05-19  
**Source**: DISPENSING → WAITING_DISPENSING rename across prototype  
**Tags**: naming, convention, queue, status

## Pattern

All queue statuses representing "waiting for X to happen" should use the `WAITING_` prefix:

| Status | Meaning |
|--------|---------|
| WAITING | รอรับบริการ (generic wait) |
| WAITING_LAB | รอผลแล็บ |
| WAITING_PAYMENT | รอชำระเงิน |
| WAITING_DISPENSING | รอจ่ายยา |

Non-waiting statuses don't get the prefix: CHECKED, IN_PROGRESS, COMPLETED, CANCELLED_*.

## Why

- Consistent grep: `grep 'WAITING_'` finds all waiting states
- Type narrowing: easy to write guards like `status.startsWith('WAITING_')`
- Self-documenting: "WAITING_DISPENSING" immediately tells you "waiting for dispensing to complete"
- Prevents naming confusion: DISPENSING vs WAITING_MEDICATION vs WAITING_DISPENSING were all used for the same concept before this fix

## Anti-pattern

Don't use action verbs as status names (DISPENSING = ambiguous — is it in progress or waiting?). Don't invent new names for the same concept in different mocks (WAITING_MEDICATION ≠ DISPENSING).
