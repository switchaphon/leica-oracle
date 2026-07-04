---
date: 2026-05-05
session: design-system-controls
tags: [parallel-agents, file-editing, risk-management]
---

# Parallel Agents on Same File: Section-Level Isolation

When dispatching multiple Chrome agents to edit the same file simultaneously, success depends on strict section-level isolation:

1. Brief each agent with exact function name boundaries (not just line numbers, which shift)
2. Explicitly state "do NOT modify any other sections"
3. After all agents complete, verify with `grep -n "type.*Controls\|interface.*Control"` that all expected definitions exist
4. Check file line count grew (not shrank — sign of overwrite)

This worked for 3 agents on a ~3000 line file because React component functions are natural isolation boundaries. Would NOT work for agents editing the same function or adjacent code.

Safer alternative for future: sequential agents or git worktree per agent.
