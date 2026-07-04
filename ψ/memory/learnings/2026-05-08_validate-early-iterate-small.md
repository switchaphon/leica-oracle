---
pattern: Validate early, iterate small — show the user after every meaningful UI change
concepts: [ux-workflow, scope-management, validation, prototype]
source: "rrr: pops-clinic-oracle"
date: 2026-05-08
---

Started with 4 small targeted fixes (fixed height, empty state, terminology, layout shift) — each took 5-10 min, Un approved immediately. Then escalated to provider selection → v2 rewrite → Chrome oracle review (2+ hours). Un saw the final result and said "แบบเก่าดูง่ายกว่า" (the old version looks simpler) — reverted.

Lesson: after every meaningful change, open the browser and show the user before moving to the next iteration. If Un had seen provider pills right after implementation, the v2 rewrite might never have happened. Simple wins. Validate early. Iterate small.
