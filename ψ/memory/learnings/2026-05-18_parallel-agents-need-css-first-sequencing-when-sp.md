---
title: Parallel agents need CSS-first sequencing. When splitting work between a Compone
tags: [team-agents, parallelism, css, file-ownership, execution-order]
created: 2026-05-18
source: rrr: pawrent-oracle
project: github.com/switchaphon/pawrent-oracle
---

# Parallel agents need CSS-first sequencing. When splitting work between a Compone

Parallel agents need CSS-first sequencing. When splitting work between a Component Agent and a Page Agent, CSS utility classes must land before the Page Agent starts. Otherwise the Page Agent uses inline styles defensively, creating drift from the shared classes. Run CSS/utility tasks first (even 30 seconds), THEN fan out page-level agents. The CSS classes are the contract — page agents should import them, not reimplement them inline.

---
*Added via Oracle Learn*
