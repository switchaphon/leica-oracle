#!/bin/bash
# Oracle fleet startup — run after reboot
# Usage: ~/ghq/github.com/switchaphon/leica-oracle/start.sh

# Leica (main + discord window)
tmux new-session -d -s 01-leica -n leica-oracle -c ~/ghq/github.com/switchaphon/leica-oracle
tmux new-window  -t 01-leica   -n leica-discord -c ~/ghq/github.com/switchaphon/leica-oracle

# Pops Clinic
tmux new-session -d -s 05-pops-clinic -n pops-clinic-oracle -c ~/ghq/github.com/switchaphon/pops-clinic-oracle

# Launch Claude Code in each
tmux send-keys -t 01-leica:leica-oracle              'claude' Enter
tmux send-keys -t 01-leica:leica-discord              'claude --dangerously-skip-permissions' Enter
tmux send-keys -t 05-pops-clinic:pops-clinic-oracle    'claude' Enter

# Attach
tmux attach -t 01-leica
