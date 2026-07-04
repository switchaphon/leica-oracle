---
date: 2026-05-08
source: "rrr --deep: pops-clinic-oracle"
tags: [complexity, simplicity, over-engineering, guide, prototype, iterative]
confidence: high
---

# Start Minimal, Add Complexity Only When Simple Proves Insufficient

Built 5 iterations of PrototypeGuide in one session: beacons → callouts → step navigation → auto-advance → triggerSelectors. Each layer created new bugs (race conditions, z-index fights, hydration mismatches, modal overlay blocking). Un said "ยังมั่วอยู่เลย หรือจะยอมถอย" — that's a verdict, not a question.

Final version: 80 lines. Beacon dots on elements + a bar with Home/title/toggle. No navigation, no auto-advance, no callouts. It works.

The reference (prototype-d2) was static HTML with scene switching. Trying to replicate that reactively against a live app with modals and portals is a fundamentally different problem. Should have recognized the gap before building, not after 5 failed iterations.

**Rule**: v1 = the simplest thing that could work. Add complexity only when users hit the wall of simplicity.
