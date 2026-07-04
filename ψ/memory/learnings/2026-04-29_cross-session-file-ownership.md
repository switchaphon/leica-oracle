# Cross-session file ownership prevents conflicts

**Date**: 2026-04-29
**Source**: pickup-queue-to-opd deep retro — 3 parallel Claude sessions
**Context**: OPD session overwrote HN badge styles in page.tsx after queue session had aligned with diag session

## Pattern

When running multiple Claude sessions on overlapping code:
1. **Assign files to sessions explicitly** — each session owns specific files, no cross-writing
2. **Announce before touching shared files** — if you must edit another session's file, relay via user first
3. **Extract to shared/ as the real fix** — relay messages align decisions but not file state; a shared component is the atomic source of truth

## Anti-pattern

Two sessions independently editing page.tsx with different style conventions, discovered only when user notices visual regression.

## Rule

- page.tsx → queue session
- opd/[id]/page.tsx → opd session
- _mock.ts → queue session (shared data, single owner)
- shared/chips.tsx → whichever session creates it first, then both consume read-only

## Broader principle

Cross-session coordination works for **decisions** (API signatures, color tokens, naming). It fails for **file state** (exact class strings, import ordering). Extract shared code to break the conflict.
