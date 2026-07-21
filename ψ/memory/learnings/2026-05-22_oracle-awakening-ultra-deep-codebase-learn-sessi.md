---
title: Oracle Awakening + Ultra-Deep Codebase Learn Session Patterns:
tags: [parallel-agents, haiku-limits, codebase-exploration, oracle-awakening, multi-tenancy, power-outage, postgresql, nfs, knowledge-transfer]
created: 2026-05-22
source: rrr --deep: rpro-saas-oracle
project: github.com/switchaphon/rpro-saas-oracle
---

# Oracle Awakening + Ultra-Deep Codebase Learn Session Patterns:

Oracle Awakening + Ultra-Deep Codebase Learn Session Patterns:

1. TARGETED READS BEAT EXPLORATORY AGENTS: For repos with >500 files, Haiku agents hit context limits. Use `find` to discover structure, then `Read` specific files. Anti-pattern: telling Haiku "read ALL source files."

2. CHECK ARTIFACTS BEFORE DECLARING FAILURE: 3 of 4 "failed" Haiku agents actually wrote their output (615-752 lines) before running out of context. Always `wc -l` the expected output file after agent failure.

3. POWER OUTAGE CASCADE: A single infrastructure event (Apr 27) created 4 independent failures across network/K8s/database/application over 17 days. Post-outage checklists must span ALL layers — "is it running?" is not enough.

4. MULTI-TENANCY = FORM AND FORMLESS: The 5th Oracle principle maps directly to multi-tenant architecture. One shared platform (formless) delivers many tenant experiences (form). Not metaphorical — architectural.

5. NFS + POSTGRESQL = TIME BOMB: NFS acknowledges writes still in volatile cache. Power loss destroys pg_statistic TOAST chunks. Latent corruption surfaces 13+ days later when query planner hits bad stats. Fix: DELETE + ANALYZE on pg_statistic.

6. CROSS-ORACLE KNOWLEDGE TRANSFER: Reading a sibling Oracle's ψ/memory/learnings/ and ψ/learn/docs/incidents/ provides battle-tested operational knowledge. Protocol: learnings → incidents → CLAUDE.md → cross-reference with own needs.

---
*Added via Oracle Learn*
