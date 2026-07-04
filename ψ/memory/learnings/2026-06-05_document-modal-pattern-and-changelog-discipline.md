# Document Modal Pattern + Changelog Discipline

**Date**: 2026-06-05
**Source**: Document modal polish session (Invoice/Receipt/Prescription + DiagnosticQuickViewDrawer)
**Confidence**: High (user-validated, DS-documented, 4 modals aligned)

## Pattern 1: Read the Reference Before Building

InvoiceModal is the canonical document modal (DS §7.11). Before creating any new modal:
1. Read InvoiceModal.tsx
2. Copy its structure (flex flex-col, 3-zone, sticky footer)
3. Check DS type scale (11px Thai min, font-semibold for H3)
4. Change only the domain-specific content

Building from scratch then fixing drift costs 5x more than copying the reference.

## Pattern 2: Changelog = 4 Surfaces

"Update changelog" means update ALL of these in one pass:
1. Main CHANGELOG array in page.tsx (version entry)
2. Per-entry changelog in each affected handoff object
3. Updated dates on touched entries
4. CHANGELOG.md (root project file)

The AI made the changes — the AI documents them. No user prompting needed.

## Pattern 3: Read Your Own Docs

Number format, design system, flow docs — if you built it, read it before defining new patterns. Don't guess formats that are already standardized. The user will catch it.

## Related

- DS Update Is Definition of Done (2026-05-12)
- Composition Over Duplication (2026-06-03)
- Modal Header Inline X Convention (2026-05-17)
