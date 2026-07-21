---
title: Session 2026-06-05: Cross-oracle learning completed full autonomous bug-fix loop
tags: [cross-oracle-learning, full-loop, jira-mcp, gitlab, maw-hey, capability-building, rpro-saas]
created: 2026-06-05
source: rrr --deep: rpro-ent-oracle
project: github.com/switchaphon/rpro-ent-oracle
---

# Session 2026-06-05: Cross-oracle learning completed full autonomous bug-fix loop

Session 2026-06-05: Cross-oracle learning completed full autonomous bug-fix loop onboarding.

1. CROSS-ORACLE PLAYBOOK TRANSFER — Ask peer oracle for worked example, not just answers. rpro-saas sent RPRO-15206 full lifecycle (Git branch model, Jira MCP workflow, deploy checklist, cherry-pick promotion, version conventions) in one thread message. Gotchas included: Jira template override, tagged-build-cant-retry rule, pnpm-workspace.yaml requirement.

2. TEST AT EVERY DEPTH — _RPRO_/rpro-enterprise/ has no .git but backend/device-service/ does. Always check one level deeper before declaring something missing.

3. FIRST REAL ISSUE > PRACTICE — RPRO-15216 (dbbackup resource limits) was first Jira issue created autonomously. Real work exercises real edge cases naturally.

4. PROGRESSION ARC — Jun 2: tool blindness discovered. Jun 5: all tools validated (Jira create/edit/comment/transition + GitLab fetch/log + maw hey). 3-day arc from blind to operational.

5. COMMUNICATION PATTERN — maw hey = real-time oracle comms (Leica teaching). /talk-to = async persistent threads. Never raw tmux send-keys.

---
*Added via Oracle Learn*
