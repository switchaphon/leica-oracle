---
title: Cross-session coordination via tmux send-keys works for parallel Claude panes ne
tags: [cross-session-coordination, tmux, parallel-agents, file-ownership, chip-extraction, prototype-design-system, column-naming, tailwind-spacing, verify-dont-declare, mirror-shape-api, all-selected-no-filter, rrr-deep]
created: 2026-04-29
source: rrr --deep: POPs-Vet (diagnostic-request-list ↔ pickup-queue-to-opd)
project: github.com/pops-vet/pops-app-vet
---

# Cross-session coordination via tmux send-keys works for parallel Claude panes ne

Cross-session coordination via tmux send-keys works for parallel Claude panes negotiating shared design tokens, API signatures, and naming conventions. Required incantation: send Escape first to clear any mode, then send the message with -l (literal) flag to prevent shell expansion, then send Enter to submit. Verify with tmux capture-pane afterward — tool result strings describe intent, not state.

Validated patterns:
- Mirror-shape APIs across siblings BEFORE extracting to shared. Both consumers independently shape components with identical prop signatures, then extraction is a 5-min lift, not a refactor.
- Color tokens stay in consumer's domain config; shared chip primitives own only shape + spacing. Domain doesn't leak into the design system.
- For multi-select filter Sets, treat selected.size === options.length as "no filter applied" — short-circuit the filter call. Gives empty Set unambiguous meaning ("show nothing").

Validated mistakes (fix going forward):
- Parallel Claude panes without file-ownership rules silently overwrite each other. A 3rd anonymous OPD pane reverted aligned chip styles 20 min after sibling agreement. Fix: declare file ownership via header comment or OWNERSHIP.md before spawning panes.
- Outer vs inner spacing confusion — when user says "spacing tight", clarify which axis: row padding (py-*), cell padding horizontal (px-*), intra-cell margin (mt-*), flex gap (gap-*).
- Don't declare completion ("✅") without verifying the actual file state with grep/cat. Tool result describes intent, not state. Especially when work crosses session/file boundaries.

Conventions established for POPs-Vet prototype/* pages:
- Sub-line gap within table cell = mt-2 (8px). Calibrated 4→12→10→8.
- Shared data concepts get shared Thai column headers: Pet=สัตว์เลี้ยง, Vet=สัตวแพทย์. Distinct events keep distinct names.
- 4-chip taxonomy: HnBadge (mono outline), CategoryPill (rounded-full + icon + colored border), Tag (text-[10px] inline), StatusBadge (same shape as CategoryPill, semantic distinction).
- HN format: HN{พศ-2digit}-{เดือน-2digit}-{running-3digit}, e.g. HN67-04-142.

---
*Added via Oracle Learn*
