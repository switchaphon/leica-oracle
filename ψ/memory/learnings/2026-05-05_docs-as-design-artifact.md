---
name: Documentation as design artifact
description: System docs should prevent confusion (not be complete) via templates + proven patterns, leaving room for outliers
type: learning
---

**Observation**: When writing a system-wide guide (like `/prototype/HANDOFF.md`), completeness is a false goal. The real goal is preventing confusion.

**The Pattern**:

The two existing prototype HANDOFFs (queue, pickup-queue-to-opd) followed the same structure. Rather than write a new individual HANDOFF, I created a *system index* that:
1. Named the pattern (flat by journey, not nested by domain)
2. Showed a template that covers 90% of cases
3. Listed what exists + what's pending (status + links)
4. Documented the reuse rules (DS first, shared second, journey-specific third)
5. Left room for outliers ("What if my journey doesn't fit flat structure?")

The goal wasn't to answer every edge case. It was to make the *existing* pattern obvious so new people don't have to guess.

**Why It Matters**:

- **Reduces friction** — next person creating a prototype copies the template, fills blanks, done. No 20-minute exploration.
- **Scales patterns** — if the flat-by-journey convention is wrong, we'll find out when someone tries to nest. Then we discuss with Leica and update the pattern. Until then, the default is set.
- **Signals what's proven** — current HANDOFFs show this structure works. Future HANDOFFs inherit that confidence.

Contrast: If I'd tried to write a "complete" guide that covered every possible journey structure, edge case, and contingency, it would be unreadable and outdated in a month.

**How to Apply**:

When documenting a system (team workflow, folder structure, design pattern):
1. Find the *existing* pattern (ask: "what have we already done?" not "what could we do?")
2. Name it (give it a clear conceptual identity)
3. Write a template for 90% (not 100%)
4. List what exists + status (inventory)
5. Document the reuse/composition rules (what goes where)
6. Leave a "when this doesn't work" escape hatch

This is what Leica does — she documents what's proven and leaves room for growth. Not micromanaging every edge case, but making the baseline clear.

---

**Source**: Session 2026-05-05, creating `/prototype/HANDOFF.md` index for pops-clinic-oracle
**Concepts**: [documentation, systems-thinking, patterns, Oracle-philosophy]
