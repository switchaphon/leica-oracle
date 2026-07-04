# Pattern Propagation Reveals SOT Drift

**Date**: 2026-05-23
**Context**: Applying appointment-flow.html template pattern to queue-flow.html
**Source**: rrr: pops-app-vet

## Lesson

When you have a well-polished reference document (appointment-flow.html) and apply its structure systematically to a sibling document (queue-flow.html), you surface inconsistencies that are invisible when documents are written independently.

Example: queue-flow.html listed FOLLOW_UP as a top-level service type alongside GENERAL_MEDICINE, SPECIALIZED_MEDICINE, and NON_MEDICAL_SERVICES. Per the SOT (SERVICE_TYPE_REFERENCE.md), FOLLOW_UP is a *subtype* of GENERAL_MEDICINE. This error had existed since the document was first created — it took pattern propagation to catch it.

## Principle

**Treat template application as an audit, not just formatting.** When aligning document B to the pattern of document A, compare every data point in B against the SOT — don't just copy the structure and keep the old data.

## Application

- After polishing one lifecycle doc, propagate the pattern to all siblings
- During propagation, verify every enum, label, and color against the canonical source
- Flag corrections separately from formatting changes so the team sees what was wrong vs what was reformatted

## Tags

documentation, pattern-propagation, sot-drift, service-types, design-system, audit
