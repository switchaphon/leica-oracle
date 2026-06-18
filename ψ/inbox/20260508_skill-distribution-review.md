---
type: reminder
from: leica
to: Un
date: 2026-05-08
status: pending
read: true
readAt: 2026-06-11T08:48:37.551Z
---

# Review: Skill Distribution Design

Un ให้ออกแบบ skill distribution per-oracle เพื่อประหยัด token.

**Design doc**: `ψ/memory/learnings/2026-05-08_skill-distribution-design.md`

**สรุปสั้น**:
- ตอนนี้: 88 skills global → ทุก oracle โหลดหมด
- ออกแบบ 5 tiers: Core(8) / Father(+25) / PM(+12) / Specialist(+1~4) / Reference(on-demand)
- Savings: 62-90% fewer skills per oracle
- Recommend: Option A (per-repo `.claude/commands/`)

**Action needed**: Un review design → approve → Leica implement migration
