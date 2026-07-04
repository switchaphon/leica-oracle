# Lesson: UX Review Before Build, Not After

**Date**: 2026-04-29
**Source**: Diagnostic-request-list prototype — built first, reviewed second, rebuilt parts
**Confidence**: High (validated through wasted effort)

## Pattern

Review the Figma design against UX heuristics BEFORE writing code. Identify improvements, get user approval, then build once — instead of build → review → rebuild.

## Sequence

1. Get Figma design
2. UX review against: Nielsen heuristics, WCAG, pops-gem principles, veterinary standards
3. Present findings with priority + effort matrix
4. User selects which to implement
5. Build with improvements included from the start

## High-impact patterns discovered

- **Clickable summary cards** = turn passive numbers into table filters (<3 clicks principle)
- **Status badges > status dots** = color + icon + text beats color-only (WCAG 1.4.1)
- **Filter feedback bar** = show active filter + count + clear button (Nielsen #1)
- **Priority indicators** = STAT vs ROUTINE visual distinction (clinical safety standard)

## User override is valid

User rejected bulk actions (#4) with domain reasoning: "1 row = 1 request, each action is independent." Framework suggestions yield to domain expertise.
