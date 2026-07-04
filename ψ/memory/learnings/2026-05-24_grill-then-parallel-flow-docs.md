# Grill-then-Parallel: Flow Documentation Pattern

**Date**: 2026-05-24
**Confidence**: High (verified in practice)
**Source**: rrr --deep: pops-clinic-oracle

## Pattern

When creating multiple related documentation artifacts:

1. **Grill first** — Use /grill-me to resolve all design decisions before writing anything. Each question should build on the previous answer. 8 rounds resolved: State vs Status, Connection sections, section ordering, OPD state badges, As-Is vs Target, exact state names, concept ownership (wait_for_result), and final confirmation.

2. **Execute in parallel** — Once decisions are locked, spawn independent agents for each file. Zero coordination needed because the grill eliminated all ambiguity.

3. **Review structure, then content** — Verify section headings first (`grep -n '<h2>'`), then spot-check critical new sections.

## Key Insights

- **Planning:Execution ratio of 3:1 is healthy** — 45 min grilling, 15 min parallel execution. The grilling IS the work; the writing is mechanical.
- **Document Target, not As-Is** — As-Is docs become throwaway work the moment you start implementing Target. Always document what you're building toward.
- **State ownership must be explicit** — Queue owns generic pipeline (CHECKED → IN_SERVICE → WAITING_PAYMENT → COMPLETED). OPD owns clinical detail (IN_PROGRESS → WAITING_DIAGNOSTIC → COMPLETED). Fuzzy ownership causes inconsistent docs.
- **Clinical intent maps to system flags** — Objective section = "I need results now" = wait_for_result=true. Plan section = "Results for next visit" = wait_for_result=false. Domain insight encoded as boolean.

## Reusable Components

- State vs Status two-card layout (lifecycle + soft-delete)
- Connection to Other Flows diagram (upstream/downstream with arrow columns)
- State Badges table (2-tone outline pattern: bg-transparent + border-{color}-300 + text-{color}-600)
- Special Rules list (rule-item pattern with icon + bold title + description)
- Static HTML flow docs (portable, no build required)
