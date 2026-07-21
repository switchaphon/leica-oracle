---
title: Session isolation is routing integrity: join-pane across tmux sessions breaks fl
tags: [architecture, fleet, tmux, session-isolation, routing]
created: 2026-05-08
source: rrr: neon-oracle
project: github.com/switchaphon/neon-oracle
---

# Session isolation is routing integrity: join-pane across tmux sessions breaks fl

Session isolation is routing integrity: join-pane across tmux sessions breaks fleet routing because resolveOraclePane assumes Pane 0 = Oracle. Each oracle must stay in its own session. Team-agents split within as temporary children.

---
*Added via Oracle Learn*
