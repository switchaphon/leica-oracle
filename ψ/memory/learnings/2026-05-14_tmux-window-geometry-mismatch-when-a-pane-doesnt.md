---
title: tmux window geometry mismatch: when a pane doesn't fill the terminal, compare pa
tags: [tmux, terminal, geometry, resize, fleet-ops, diagnostic]
created: 2026-05-14
source: rrr --deep: rpro-ent-oracle
project: github.com/switchaphon/rpro-ent-oracle
---

# tmux window geometry mismatch: when a pane doesn't fill the terminal, compare pa

tmux window geometry mismatch: when a pane doesn't fill the terminal, compare pane size (list-panes) with client size (list-clients). Fix with `tmux resize-window -t <session:window> -A` to force aggressive refit. Root cause: tmux doesn't always recompute window size after terminal geometry changes, even with window-size=latest. Diagnostic workflow: list-panes → list-clients → display-message → resize-window -A.

---
*Added via Oracle Learn*
