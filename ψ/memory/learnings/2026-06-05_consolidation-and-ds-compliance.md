# Consolidation as Drift Prevention + DS Compliance Discipline

**Date**: 2026-06-05
**Source**: rrr --deep: pops/app/vet
**Confidence**: High (confirmed across 3 sessions)

## Patterns

### 1. Shell-wraps-body eliminates drift (High confidence)
When multiple routes share 80%+ of a page, create a thin shell that delegates to the shared body component. OpdOrderFlowShell went from 97 lines (duplicated UI) to 13 lines (pure delegation). Button-label drift disappeared immediately.

**Reuse**: Any time a new route variant is created for an existing page.

### 2. DS compliance check before shipping (High confidence)
Three violations shipped in first drafts this week: text-[10px] (should be 11px Thai min), font-bold (should be font-semibold), non-sticky footers. All caught by user, not by AI. Need a pre-ship checklist: typography minimums, font weights, sticky footer, neutral-* tokens, dot separator format.

**Reuse**: Every UI commit in this prototype.

### 3. Pure-function resolvers bridge prototype to production (Medium confidence)
`orderOriginResolver.ts` isolates business rules with zero React dependencies and explicit PRD references. This makes prototype logic unit-testable and directly portable to production without refactoring.

**Reuse**: Any prototype component with non-trivial decision logic.

### 4. Batch polish after feature merges (Medium confidence)
Scattered fix commits (radius, icons, labels, badge width) are symptoms of not doing a single polish pass after each feature merge. A checklist-driven sweep catches 5 issues in 1 commit.

**Reuse**: After every feature merge or multi-commit feature session.

### 5. InvoiceModal is the canonical document modal (High confidence)
DS 7.11 codifies the pattern: dot-separator title, section labels, category-aggregated line items, sticky footer, 11px Thai min. All new document modals (receipt, prescription, certificate) should copy structure, change only domain content.

**Reuse**: Every new document/printable modal.

## Connections
- Confirms [[oracle-identity-and-design-system]] (DS as tiebreaker)
- Confirms [[document-modal-pattern-and-changelog-discipline]] (InvoiceModal as reference)
- Extends [[two-page-mockup-over-state]] (shell-wraps-body is the multi-route version)
