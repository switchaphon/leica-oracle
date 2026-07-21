---
title: When delegating to subagents (Chrome, Flux, etc.), never paraphrase grilled deci
tags: [delegation, grilled-decisions, subagents, verification, semantic-drift]
created: 2026-05-18
source: rrr: pawrent-oracle
project: github.com/switchaphon/pawrent-oracle
---

# When delegating to subagents (Chrome, Flux, etc.), never paraphrase grilled deci

When delegating to subagents (Chrome, Flux, etc.), never paraphrase grilled decisions. Copy exact decision tables, level titles, weight percentages, and toggle names verbatim into the agent brief. Subagents have no memory access — they only know what the brief contains. If a grill locked "🐾 ทาสใส่ใจ" and you brief "Learning", the agent will use "Learning". CI gates catch syntax, not semantic drift from grilled decisions.

---
*Added via Oracle Learn*
