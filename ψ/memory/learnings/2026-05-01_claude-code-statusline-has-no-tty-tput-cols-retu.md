---
title: Claude Code statusline has no TTY — tput cols returns 80, $COLUMNS is 0. Real wi
tags: [statusline, claude-code, terminal, tmux, width-detection, fleet-config, maw]
created: 2026-05-01
source: rrr --deep: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Claude Code statusline has no TTY — tput cols returns 80, $COLUMNS is 0. Real wi

Claude Code statusline has no TTY — tput cols returns 80, $COLUMNS is 0. Real width detection chain: $COLUMNS (if >0) → stty size </dev/tty → tmux #{pane_width} → fallback 120. Also: tmux session groups constrain to smallest client width, so multi-screen setups always get the narrow dimension. Fleet config contract: project_path + icon + short_name fields make an Oracle visible in the statusline.

---
*Added via Oracle Learn*
