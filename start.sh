#!/bin/bash
# Oracle fleet startup — run after reboot
# Usage: ~/ghq/github.com/switchaphon/leica-oracle/start.sh
#
# Token switching: run `maw token use <name>` BEFORE this script.
# All sessions will use the same token from leica-oracle/.envrc

# Load token from .envrc (shared across all sessions)
cd ~/ghq/github.com/switchaphon/leica-oracle
eval "$(direnv export bash 2>/dev/null)"
TOKEN_CMD="export CLAUDE_CODE_OAUTH_TOKEN='$CLAUDE_CODE_OAUTH_TOKEN' CLAUDE_TOKEN_NAME='$CLAUDE_TOKEN_NAME'"

# Leica (main + discord window)
tmux new-session -d -s 01-leica -n leica-oracle -c ~/ghq/github.com/switchaphon/leica-oracle
tmux new-window  -t 01-leica   -n leica-discord -c ~/ghq/github.com/switchaphon/leica-oracle

# Pops Clinic
tmux new-session -d -s 05-pops-clinic -n pops-clinic-oracle -c ~/ghq/github.com/switchaphon/pops-clinic-oracle

# Per-oracle Discord state dirs (each oracle has its own bot token in .discord-state/.env)
LEICA_DISCORD="export DISCORD_STATE_DIR=~/ghq/github.com/switchaphon/leica-oracle/.discord-state"
POPS_DISCORD="export DISCORD_STATE_DIR=~/ghq/github.com/switchaphon/pops-clinic-oracle/.discord-state"

# Launch Claude Code with shared token + per-oracle Discord identity
tmux send-keys -t 01-leica:leica-oracle              "$TOKEN_CMD && $LEICA_DISCORD && claude" Enter
tmux send-keys -t 01-leica:leica-discord              "$TOKEN_CMD && $LEICA_DISCORD && claude --dangerously-skip-permissions" Enter
tmux send-keys -t 05-pops-clinic:pops-clinic-oracle    "$TOKEN_CMD && $POPS_DISCORD && claude" Enter

# Attach
tmux attach -t 01-leica
