# Lesson: Prototype Workflow Patterns for Designer-as-Prompter

**Date**: 2026-04-29
**Source**: Prototype workflow design session with Witchaphon
**Confidence**: High (decisions agreed, not yet validated in practice)

## Patterns

### 1. Actual route over route group for isolated work
When a set of pages needs different middleware behavior (e.g., no auth), use an actual route segment (`app/prototype/`) not a route group (`app/(prototype)/`). Route groups share middleware with siblings; actual routes can be excluded with one matcher pattern.

### 2. Split metadata and detail across two artifacts
Dashboard needs lightweight metadata (status, name, links) → data.js. Developers need detailed handoff (mock mapping, components, decisions) → HANDOFF.md per folder. Neither duplicates the other. Dashboard links to HANDOFF.md for depth.

### 3. Reuse existing documentation patterns
Before designing a new artifact format, check what the project already does. pops/vet had a proven HTML+data.js pattern in docs/ (qa-report, rbac-design, reports-design). Adopting it means zero learning curve and visual consistency.

### 4. Branch isolation by audience
prototype branch → develop (prototype files live here) → main (production only). The key insight: main should never contain exploration artifacts. Develop is the staging ground where prototype and production code coexist temporarily.

### 5. Consistent templates reduce cognitive load
HANDOFF.md uses the same sections in the same order for every journey. Component status uses only NEW/REUSE. No emoji variation. Dev opens any HANDOFF.md and knows exactly where to look.

## Connections

- This pattern could be reused by pawrent-oracle (sibling Project PM) for LINE LIFF prototyping
- The HTML+data.js dashboard pattern is the same as docs/qa-report — may warrant a shared template
- Designer-as-prompter workflow may inform how future non-developer Oracle users interact with project repos
