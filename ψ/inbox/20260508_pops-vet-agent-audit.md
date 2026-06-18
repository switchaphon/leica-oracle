---
from: leica (Father Oracle)
date: 2026-05-08
type: audit-result
subject: pops/vet agent consolidation — 24 → 6
status: pending-review
read: true
readAt: 2026-06-11T08:48:37.551Z
---

# pops/vet Agent Audit

24 agents defined, only 2 ever used (chrome built-in + code-reviewer).
11 duplicate pairs. 22 agents never invoked.

## Recommendation: 24 → 6

Keep: code-reviewer, qa-tester, ux-designer, shadcn-helper, git-commit-helper
Delete: 14 agents (staff-engineer, system-architect, team-lead, product-manager, etc.)
Merge: 3 shadcn agents → 1, 2 ux agents → 1, 2 reviewer agents → 1

Full design: see skill-distribution-design.md for overall token optimization plan.
Implement together with skill distribution when Un is ready.
