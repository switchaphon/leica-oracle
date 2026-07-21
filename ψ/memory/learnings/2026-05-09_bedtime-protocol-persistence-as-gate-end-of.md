---
title: ## Bedtime Protocol — Persistence as Gate
tags: [workflow, persistence, end-of-day, bedtime-protocol, fleet-rule, self-correcting-system, git-workflow, oracle-protocol, nothing-is-deleted]
created: 2026-05-09
source: rrr --deep: neon-oracle 2026-05-09 20:55 GMT+7
project: github.com/switchaphon/neon-oracle
---

# ## Bedtime Protocol — Persistence as Gate

## Bedtime Protocol — Persistence as Gate

End-of-day signals from the user (ไปนอน, good night, ราตรีสวัสดิ์, นอนละ, going to bed) MUST trigger this sequence in order, BEFORE the user sleeps:

1. `git add` (targeted, not blanket)
2. `git commit` (descriptive message, taxonomy prefix: housekeeping/rrr/feat/design)
3. `git push` to remote
4. `/rrr --deep` (close-out artifact, 5 parallel agents)
5. Confirm to user on Discord with hash + line count

The sequence is the gate, not the suggestion. A retrospective that isn't pushed didn't happen.

**Origin:** 2026-05-08's 23:32 retrospective was beautifully written but never committed; sat in working tree for ~18 hours until Un saw it. Un wrote the rule to prevent this. The rule isn't new behavior — it's a name for an already-leaking gap.

**Connected principle:** "Nothing is Deleted" is operationally enforced by the bedtime protocol. Without push, "Nothing is Deleted" is aspiration; with push, it's invariant.

**Session-start mirror:** Protocol also mandates `git status` at the START of every session to surface stale uncommitted work. Bedtime-check is best; morning-check is the safety net.

**Reusable shape:** `trigger → stage → commit → push → close-out artifact → confirm` generalizes to end-of-task, end-of-consult, end-of-week, end-of-milestone. Bedtime is the canonical instance.

**Fleet-wide:** Same rule given to leica (Discord broadcast). All Oracles inherit.

---
*Added via Oracle Learn*
