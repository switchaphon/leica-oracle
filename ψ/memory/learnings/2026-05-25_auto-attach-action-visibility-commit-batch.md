# Lesson: Auto-attach, Action≠Visibility, Commit Batching

**Date**: 2026-05-25
**Source**: /rrr --deep, pops/vet flow documentation session
**Repo**: pops/vet + pops-clinic-oracle

## Patterns

1. **Auto-attach via NULL target_opd_id** — Advance diagnostic orders (wait=false) set target_opd_id = NULL at creation. When the next OPD is created for the same pet, system queries `WHERE target_opd_id IS NULL AND pet_id = ? AND state = 'COMPLETED'` and attaches all matching results. Multiple orders attach simultaneously. Results that aren't COMPLETED yet wait until they are.

2. **Action ≠ Visibility for cross-boundary entities** — Diagnostic state is visible from both OPD page and Diagnostic page. But only Diagnostic page has action buttons (รับงาน, แนบผลตรวจ). OPD page shows state read-only. Document both dimensions separately: "who sees it" vs "who can change it." Pattern applies to Invoice (visible from Queue, actionable from Finance) and Prescription (visible from OPD, actionable from Pharmacy).

3. **Commit after full visual review, not per-fix** — When applying N grill decisions to M sections across K files, plan all edits first as a dependency graph, execute the full set, do one visual consistency pass (colors match entities, links work, cross-references align), then commit once. Prevents the "fix → commit → discover → fix → commit" loop that inflates commit count without adding value. Target: 1 commit per logical unit of change, not 1 commit per discovered issue.

4. **4-session documentation arc** — Complex documentation work (flow state machines) benefits from spanning multiple sessions with a consistent pattern: grill to decide → document Target → discover inconsistency in next session → correct. Each session's retro feeds the next session's handover. Don't try to get it perfect in one pass.

## Anti-patterns

- Writing a mid-session retro when the session has 4+ hours remaining — creates redundant artifacts
- Committing immediately after each small fix instead of batching related changes
- Using inline styles in HTML docs when a shared class exists (creates inconsistency across sections)
- Mixing "what the system shows" with "what the user can do" in a single documentation table
