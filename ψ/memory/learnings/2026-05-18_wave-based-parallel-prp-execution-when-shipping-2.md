---
title: Wave-based parallel PRP execution: When shipping 2-3 independent PRPs, use 3 wav
tags: [parallel-agents, prp-pipeline, wave-execution, team-coordination, file-ownership, grilled-decisions]
created: 2026-05-18
source: rrr --deep: pawrent-oracle
project: github.com/switchaphon/pawrent-oracle
---

# Wave-based parallel PRP execution: When shipping 2-3 independent PRPs, use 3 wav

Wave-based parallel PRP execution: When shipping 2-3 independent PRPs, use 3 waves — (1) Foundation: migrations + types + test fixtures sequentially, (2) Parallel: one agent per PRP with strict file ownership on shared branch, (3) Integration: lead agent wires shared files + quality gates. Proven shipping Phase 2A Diary + Phase 2B ID Card in ~60 min. Pre-grilled decisions (25 locked across 2 PRPs) eliminated all mid-execution ambiguity. PRP validation step caught 2 critical gaps (missing table DDL, incorrect "existing" route claim) that would have been production blockers.

---
*Added via Oracle Learn*
