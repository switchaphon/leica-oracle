# Swimlane Diagrams Reveal Entity Boundaries That Flat State Machines Hide

**Date**: 2026-05-26
**Source**: rrr --deep: pops-clinic-oracle
**Confidence**: High (validated by Un catching the WAITING_DISPENSING misattribution)

## Pattern

When multiple entities (Queue, Invoice, Prescription) change state in response to the same user action, a **swimlane diagram** with one lane per entity makes the boundaries immediately clear. A flat state machine (all nodes on one row) conflates entity states with system steps.

## Evidence

Prescription flow doc had 3 states: `PRESCRIBED → WAITING_DISPENSING → DISPENSED`. During grill session, Un identified that WAITING_DISPENSING is a **Queue state**, not a Prescription state. Prescription only has 2 states: `PRESCRIBED → DISPENSED`.

The flat diagram made this invisible because all states were on one row with scope labels. The swimlane diagram (Queue lane / OPD lane / Prescription lane) made the entity boundary obvious — WAITING_DISPENSING sits in the Queue lane, not the Prescription lane.

## Reusable Techniques

1. **Swimlane for cross-entity flows** — one lane per entity, nodes left→right by time, cross-lane dashed arrows for triggers
2. **Reference schema as gap-finder** — use external DB schema to find gaps in existing docs without replacing the structure. "Keep our model, adopt their insights."
3. **Grill before parallel execution** — lock all decisions (7 questions) before spawning agents. Prevents agents from making architectural choices.
4. **Agent stop criteria for visual work** — SVG agents need explicit "done" conditions, otherwise they iterate endlessly on visual tweaks.

## Anti-pattern

Naming a state by what it affects ("prescription is waiting") instead of what entity owns it ("Queue is in WAITING_DISPENSING"). The entity that transitions owns the state name.

## Tags

swimlane, state-machine, entity-boundary, flow-docs, grill-before-execute, visual-documentation
