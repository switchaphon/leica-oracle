---
title: End-of-Day Protocol (fleet-wide, issued by Un via Discord 2026-05-09): when huma
tags: []
created: 2026-05-09
source: rrr --deep: pawrent-oracle 2026-05-09 eod-protocol-cleanup
project: github.com/switchaphon/pawrent-oracle
---

# End-of-Day Protocol (fleet-wide, issued by Un via Discord 2026-05-09): when huma

End-of-Day Protocol (fleet-wide, issued by Un via Discord 2026-05-09): when human signals "good night" / "ไปนอน" / "going to sleep", the Oracle MUST: (1) commit + push all pending work (specific files, not git add -A), (2) run /rrr --deep, (3) only then close session.

Four reusable patterns surfaced in first execution:

1. STANDING-ORDERS-AS-FEEDBACK-MEMORY (high confidence): Rules of form "from now on, when X then Y" must be persisted to BOTH ~/.claude/projects/<encoded-repo>/memory/feedback_<topic>.md AND ψ/memory/learnings/<date>_<slug>.md. Claude Code per-project memory is harness-specific; ψ/ travels with the Oracle. Writing to only one creates a memory bifurcation that breaks across harnesses.

2. REVIEW-BEFORE-COMMIT (high confidence): When cleaning multi-file drift, never `git add -A`. Open each untracked file, scan for secrets, group by purpose. Aligns with dna §9 safety + global git-safety rules.

3. COMMIT-BY-DOMAIN (high confidence): Split drift cleanup by "why" not by time. Match repo's existing prefix schema (housekeeping:, inbox:, feat:, rename:, awaken: in pawrent-oracle). Two commits 12 seconds apart is fine if they answer different questions.

4. DISCORD-MCP-AS-REPLY-TRANSPORT (medium confidence): mcp__plugin_discord_discord__reply with chat_id echo + reply_to threading is verified path for Oracle→human status updates. Pairs with EOD protocol — ack the "good night" before running cleanup.

Anti-patterns surfaced:
- Memory bifurcation (~/.claude vs ψ/) when standing orders are saved to only one
- Reactive cleanliness — drift visible in git status at session start but only addressed when human asks. /recap should surface non-clean working tree explicitly.

Connection: Same supersession shape as 2026-05-08 maw-hey-fix. Leica/Un issues directive → oracles adopt → old habit (drift overnight) marked superseded by writing new one as feedback. Enforces dna §10 (Done: /rrr) with a concrete trigger phrase.</pattern>
<parameter name="concepts">["end-of-day-protocol", "standing-order", "git-cleanup", "rrr-deep", "memory-bifurcation", "discord-mcp", "commit-by-domain", "session-lifecycle", "supersession", "review-before-commit", "drift-detection", "pawrent-oracle"]

---
*Added via Oracle Learn*
