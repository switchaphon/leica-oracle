---
name: Timeline card collapse pattern
description: Collapse detail sections into timeline step cards with action buttons to reduce drawer scroll — proven pattern from queue drawer, applied to diagnostic
type: learning
date: 2026-05-17
source: rrr
---

When a drawer has a large detail section (test table, prescription list, order items) that causes excessive scrolling, collapse it into the relevant timeline step's info card:

1. Show a summary line in the card (e.g., "CBC, Chem 12, Calcium, T4")
2. Add a source tag (In-House/External) for context
3. Add an action button ("ดูรายการตรวจ") that opens a modal with full details
4. The modal serves as a self-contained work order — complete enough that the reader doesn't need to go back to the drawer

This pattern was established in the queue drawer (QuickViewDrawer.tsx) and successfully applied to the diagnostic drawer. The TimelineEntry interface was extended with `onAction?: () => void` to support this.

**When to apply**: Any drawer where a section is purely informational (read-only detail) and takes >200px of scroll space.
**When NOT to apply**: When the section requires inline interaction (form fields, checkboxes, drag-and-drop).
