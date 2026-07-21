---
title: Never upgrade shared infrastructure (maw, CLI tools) without verifying the depen
tags: [maw, infrastructure, upgrade-safety, rollback, dependency-chain]
created: 2026-04-30
source: rrr: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Never upgrade shared infrastructure (maw, CLI tools) without verifying the depen

Never upgrade shared infrastructure (maw, CLI tools) without verifying the dependency chain. maw v26.4.53 moved 62 plugins to an unreachable online registry, breaking all critical commands (bud, wake, ls, capture). Always: read changelog → dry-run → verify top 5 commands → know rollback command before starting. Pinned safe version: v26.4.31.

---
*Added via Oracle Learn*
