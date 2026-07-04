---
name: Mock data as design artifact
description: Design mock data as carefully as UI — it catches edge cases that code review misses (conditional steps, document identity, status contradictions)
type: learning
confidence: high
session: 2026-05-17 queue lifecycle overhaul
concepts: [mock-data, prototyping, edge-cases, design-review]
---

## Pattern

Mock data is not filler — it's a design verification tool. When building prototype flows, the mock data matrix should cover every lifecycle combination systematically. Three examples from this session:

1. **Conditional timeline steps**: Showing "รอจ่ายยา" (dispensing) on every queue implied every visit gets medication. Only by building cases WITH and WITHOUT prescriptions (q3 vs q4) did this assumption surface.

2. **Document identity**: Invoice and receipt were modeled as separate actions until /grill-me revealed they're the same document at different lifecycle stages. One button, label changes by state.

3. **Status contradiction**: Diagnostic request #11 had status COMPLETED in the table but CANCELLED in the drawer — only caught because the mock data was reviewed case-by-case.

## How to apply

Before building UI for any lifecycle flow:
1. List all status combinations as a matrix (status x entry-type x optional-branches)
2. Create one mock case per combination with realistic data
3. Review the mock data for logical consistency BEFORE wiring to UI
4. Conditional steps (lab, dispensing) should NOT appear as default pending — only when the condition is met
