---
pattern: When multiple locations drift repeatedly, eliminate locations instead of automating sync between them
context: Changelog had 3 locations (CHANGELOG.md, page.tsx CHANGELOG[], per-flow handoff.changelog[]) causing drift every session for 5+ weeks. 6 feedback memories accumulated about the same problem. Fix = delete CHANGELOG.md, consolidate to 1 file (page.tsx).
resolution: Same principle applied to DESIGN.md (deleted 06-08). When you keep adding reminders about a process, the process is wrong — fix the structure, not the reminders.
tags: [single-source-of-truth, process-design, documentation, changelog]
---

## Pattern: Eliminate sync, don't automate it

When N locations must stay in sync and they keep drifting:
- Don't add a script/hook to sync them
- Don't add more reminders to memory
- Delete N-1 locations and keep 1 as canonical

Applied twice in this project:
1. DESIGN.md deleted 06-08 → design-system/page.tsx is canonical DS
2. CHANGELOG.md deleted 06-11 → page.tsx CHANGELOG[] + per-flow is canonical changelog

Meta-pattern: 6 feedback memories about the same problem over 5 weeks = structural problem, not discipline problem.
