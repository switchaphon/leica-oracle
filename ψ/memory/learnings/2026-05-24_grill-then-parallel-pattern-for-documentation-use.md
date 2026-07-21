---
title: Grill-then-Parallel pattern for documentation: Use /grill-me to resolve all desi
tags: [grill-me, parallel-agents, flow-documentation, state-machine, target-architecture, documentation-pattern]
created: 2026-05-24
source: rrr --deep: pops-clinic-oracle
project: github.com/switchaphon/pops-clinic-oracle
---

# Grill-then-Parallel pattern for documentation: Use /grill-me to resolve all desi

Grill-then-Parallel pattern for documentation: Use /grill-me to resolve all design decisions (8 rounds in this case) before spawning parallel agents to write. Planning:Execution ratio of 3:1 is healthy. Key insights: (1) Document Target architecture, not As-Is — As-Is becomes throwaway work. (2) State ownership must be explicit — Queue owns generic pipeline (IN_SERVICE), OPD owns clinical detail (WAITING_DIAGNOSTIC). (3) Clinical intent maps to system flags — Objective=wait_for_result=true, Plan=wait_for_result=false. (4) State vs Status pattern (lifecycle + soft-delete) applies uniformly across entities.

---
*Added via Oracle Learn*
