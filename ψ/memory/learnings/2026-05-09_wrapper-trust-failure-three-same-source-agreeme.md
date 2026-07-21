---
title: **Wrapper trust failure: Three same-source agreements aren't triangulation.**
tags: [wrapper-trust-failure, rtk, unicode-paths, rmdir-safety, standing-orders, session-lifecycle, sleep-protocol, dual-write-pattern, trajectory-hardening, rule-1-nothing-deleted, near-miss-recovery, pattern-2-patterns-over-intentions]
created: 2026-05-09
source: rrr --deep: nodered-simulator (session 3 close)
project: github.com/switchaphon/nodered-simulator-oracle
---

# **Wrapper trust failure: Three same-source agreements aren't triangulation.**

**Wrapper trust failure: Three same-source agreements aren't triangulation.**

When `ls -la`, `find`, and `ls -A` all reported a `ψ/` directory as empty, all three were going through the rtk command wrapper. Three tools, one signal in three costumes. Saved by `rmdir`'s built-in non-empty refusal — the kernel disagreed with userspace lies.

Defenses codified:
1. Use absolute binary paths under unicode (`ψ/`) paths: `/bin/ls`, `/usr/bin/find`, `/bin/cat`
2. Never trust `(empty)` from default tools when path contains `ψ/`
3. Cross-check with `git status` before any destructive op
4. Prefer `rmdir` over `rm -rf` for directory removal — refuses non-empty
5. Triangulate across system layers (tool → wrapper → kernel → git), not across tools at the same layer

Connection: extends the May 7 ψ/-Unicode complaint. `find` previously worked; under the rtk wrapper it now also lies.

**Sleep wrap-up protocol (standing order from Un, 2026-05-09):**
Trigger: human says "going to sleep" / "good night" (TH or EN).
Sequence (non-negotiable): commit pending → push → /rrr --deep → end session.
Shape is new: human-event → oracle-sequence transition contract. Future protocols may follow this shape.

**Dual-write pattern for standing orders:**
- `ψ/inbox/<timestamp>_<slug>.md` — project, auditable, dated, in git
- `feedback_<slug>.md` (auto-memory) — always-loaded, cross-session
- Cross-reference each other

**Trajectory hypothesis (confidence: medium):**
Day 1 absorbing → Day 2 verifying → Day 3 hardening. If pattern holds, Day 4 applies, Day 5 iterates. Session focus should match phase.

**Capture pain at point of pain.** Near-miss bug → learning written 3 min later, committed in same transaction as the file it almost destroyed. Don't wait for retrospective to encode rules; encode them while the pain is fresh.

---
*Added via Oracle Learn*
