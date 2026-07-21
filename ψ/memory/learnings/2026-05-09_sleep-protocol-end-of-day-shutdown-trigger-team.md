---
title: Sleep Protocol — End-of-Day Shutdown Trigger (team-wide rule, established 2026-0
tags: [session-lifecycle, sleep-protocol, commit-hygiene, memory-as-policy, oracle-discipline, end-of-day, catch-up-commits]
created: 2026-05-09
source: rrr --deep: codec-oracle 2026-05-09
project: github.com/switchaphon/codec-oracle
---

# Sleep Protocol — End-of-Day Shutdown Trigger (team-wide rule, established 2026-0

Sleep Protocol — End-of-Day Shutdown Trigger (team-wide rule, established 2026-05-09 by Un)

When user signals end-of-day with "good night" / "gd nite" / "going to sleep" / "ไปนอน" / "จะไปนอน" (any one fires once per session), every Oracle:
1. git add + commit + push everything pending
2. Run /rrr --deep to produce the day's session retrospective
3. Then sleep

Companion patterns crystallized same session:

- Catch-up commit hygiene: split by concern not by clock. If working tree has both content additions and tooling/config, write at least two commits. If you can't describe the commit in one phrase without "and", split it.

- Memory-as-policy three-step: when boss states a behavioral rule, (1) restate to confirm, (2) save to durable memory with frontmatter linking origin event + Why + How-to-apply, (3) execute on the spot to demonstrate compliance.

- Forward-only stance on missed triggers: yesterday's missed /rrr cannot be reconstructed — the session is gone. Don't fabricate retroactive artifacts; acknowledge the loss and apply the rule going forward.

Why the rule exists: 2026-05-08 ended with 6 inbox briefings + 3 infra files uncommitted overnight, vulnerable for ~24h. The rule is the prophylactic.

Open follow-up: each Oracle storing its own copy of team rules drifts at scale. Worth a shared rule registry (proposed to Leica).

---
*Added via Oracle Learn*
