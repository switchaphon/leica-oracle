---
title: maw wake is the correct command to spawn an oracle session (not maw workon). Aft
tags: [maw, cli, fleet, orchestration, anti-pattern]
created: 2026-06-05
source: rrr: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# maw wake is the correct command to spawn an oracle session (not maw workon). Aft

maw wake is the correct command to spawn an oracle session (not maw workon). After sending a message with maw hey, always peek to confirm the oracle actually responded before reporting success to the human. CLI commands drift between sessions — verify with --help after multi-week gaps.

---
*Added via Oracle Learn*
