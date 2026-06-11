# Match ceremony to urgency

**Date**: 2026-06-10
**Source**: rrr: leica-oracle
**Context**: Un said "start now, are you ready to rock?" while Leica was stuck in plan mode writing formal plans

## Pattern

When the user describes a task with enough specificity ("Rust Discord Bot — install rustup, cargo init, build with no unwrap, unit tests"), a formal plan-write-review cycle adds friction without adding clarity. The user already has the plan in their head — they want execution, not documentation.

Conversely, when a task is ambiguous or high-stakes, the ceremony prevents wasted work.

## Heuristic

- User gives specific steps + says "start" → skip plan mode, execute directly
- User gives vague goal + no urgency → plan mode adds value
- User rejects ExitPlanMode more than once → they want action, not approval flows

## Tags

workflow, plan-mode, user-experience, friction, ceremony
