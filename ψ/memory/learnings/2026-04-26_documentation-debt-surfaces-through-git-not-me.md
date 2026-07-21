---
title: ## Documentation Debt Surfaces Through Git, Not Memory
tags: [documentation, git, changelog, audit, parallel-agents, technical-debt, prp, maintenance]
created: 2026-04-26
source: rrr: nodered-simulator
---

# ## Documentation Debt Surfaces Through Git, Not Memory

## Documentation Debt Surfaces Through Git, Not Memory

When a CHANGELOG has version gaps, the git log is always the source of truth. A 30-second `git log --all | grep merge` surfaces shipped-but-undocumented work immediately — no amount of memory or documentation review catches it faster.

**The silent gap pattern**: Feature written → shipped → CHANGELOG gets "do it later" → later never comes → gap becomes part of the project's mental model ("docs are approximately right"). Caught only during dedicated housekeeping sessions.

**Parallel agent audits have complementary blind spots**: Architect, Guardian, and QA agents each see through a different lens with limited overlap. Architect found registry restart problem. Guardian found CSRF bypass. QA found vm-sandbox harness gap. None of these overlapped. Running all three in parallel (not sequentially) is worth the time precisely because no single lens catches everything.

**PRP status fields decay fast**: Archive by location (done = archive/) is more reliable than updating status strings in files. The location tells the truth even when the content lies.

**How to apply**:
- Start of any housekeeping session: compare `git log --oneline` count to CHANGELOG entry count. If they diverge, find the gap.
- After an audit: run at least 2 different agent types (architect + guardian, or guardian + QA).
- PRP lifecycle: write → execute → archive. Don't trust status fields.


---
*Added via Oracle Learn*
