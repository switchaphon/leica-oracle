---
title: Each Oracle must stay in its own tmux session. Split panes within a session are 
tags: [session-architecture, tmux, team-agents, routing, oracle-design]
created: 2026-05-08
source: rrr: leica-oracle 2026-05-08
project: github.com/switchaphon/leica-oracle
---

# Each Oracle must stay in its own tmux session. Split panes within a session are 

Each Oracle must stay in its own tmux session. Split panes within a session are for team-agents only. Never join-pane across sessions — it breaks fleet routing. resolveOraclePane routes to Pane 0 (Oracle main pane), team-agents take higher indexes. Use maw peek or maw a to observe other oracles.

---
*Added via Oracle Learn*
