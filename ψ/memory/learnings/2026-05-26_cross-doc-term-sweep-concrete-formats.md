# Cross-Doc Term Alignment + Concrete Data Formats

**Date**: 2026-05-26
**Source**: rrr --deep: pops-clinic-oracle
**Confidence**: High (validated in session)

## Pattern 1: Cross-Doc Term Sweep

When a field name or key term changes in one document, immediately grep all sibling documents and update atomically in the same commit. The pattern-propagation-as-audit principle (from 2026-05-23) applies at the term level too.

**Example**: `target_opd_id` → `target_visit_no` changed in diagnostic-flow.html SVG diagrams but was missed in overall-flow.html (5 locations), trigger table (2 rows), and wait_for_result logic section. Caught during cross-reference review, required a follow-up commit.

**Technique**: After any term rename, run `grep -rn "old_term" docs/` across all sibling docs before committing.

**Anti-pattern**: Incremental rename across sessions — creates a dual-term window where readers see both names and don't know which is canonical.

## Pattern 2: Concrete Data Formats Over Abstract Placeholders

Use real system data formats in diagrams instead of abstract labels like "A", "B", "Visit 1", "Visit 2".

**Example**: `VN69-05-0042` (visit_no pattern: YY-MM-XXXX) instead of "Visit A". The reader sees the actual system format, understands the month-based numbering, and can map it to their mental model of clinic operations.

**When to apply**: Any diagram that shows data fields, IDs, or references between entities. Especially useful for:
- Foreign key relationships (source_visit_no → target_visit_no)
- Time-based patterns (VN69-05 = May, VN69-06 = June → cross-month advance orders)
- Auto-attach/auto-link mechanisms

## Pattern 3: SQL Inside SVG Annotations

For data model flow diagrams, embedding the exact SQL query inside an SVG annotation box (below the swimlane) makes the mechanism unambiguous.

**Technique**: Use a divider line inside the annotation rect, then monospace `<text>` elements for each SQL line. Color the SQL in the lane's accent color.

```svg
<line x1="452" y1="296" x2="858" y2="296" stroke="#93c5fd" stroke-width="1" opacity="0.5"/>
<text x="455" y="312" font-size="9" fill="#1e40af" font-family="monospace">UPDATE diagnostic_order</text>
```

**When to apply**: Auto-attach, auto-create, cascade update — any mechanism where "the system does X when Y happens" benefits from showing the exact operation.

## Connections

- Extends `2026-05-23_pattern-propagation-reveals-drift.md` (template propagation as audit → now applies to term renames too)
- Extends `2026-05-26_swimlane-entity-boundary-grill-pattern.md` (swimlane coordinate-comment template now includes concrete data format guidance)
- Reinforces `feedback_post_commit_checklist.md` (add "grep renamed terms across all docs" to the checklist)

## Tags

cross-reference, term-alignment, data-format, svg-annotation, documentation, flow-docs
