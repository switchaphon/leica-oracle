# Lesson: Start state machine revisions from the transition table

**Date**: 2026-06-10
**Context**: Revising diagnostic order state machine Rev 4 — DRAFT as single entry point
**Source**: rrr: pops-clinic

## Observation

When revising a state machine documented across multiple formats (SVG diagrams, prose descriptions, transition tables, cascade rules), the transition table is the canonical source. If the table is correct, everything else can be derived.

## Lesson

Start with the transition table (§8), get it right, then use it as the spec for updating SVGs, badge tables, prose, and invariants. This prevents inconsistencies where a diagram shows a path that the table doesn't list, or vice versa.

## Also

Single entry point > dual entry point for state machines. The old design (PLANNED or DRAFT as entry) created ambiguity. The new design (always DRAFT, then fork) is easier to reason about for both documentation and implementation.

## Tags

state-machine, documentation, design-patterns, diagnostic-order
