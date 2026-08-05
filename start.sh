#!/bin/bash
# Oracle fleet startup — run after reboot.
# Usage: ~/ghq/github.com/switchaphon/leica-oracle/start.sh
#
# Token handling changed 2026-08-05. This script no longer exports
# CLAUDE_CODE_OAUTH_TOKEN into the panes it spawns. It used to read leica's
# token and inject it into every pane including pops-vet's — the cross-account
# bleed that was fixed on 2026-07-29. Each repo's own .envrc supplies its own
# token via direnv:
#
#   leica, pops-pet, pops-vet, vets-hub  -> trio
#   chrome, codec, neon, relay, rpro-ent -> un
#   nodered-simulator                    -> tul
#   rpro-saas                            -> kla
#
# Panes are opened with NO command, so tmux starts an interactive login shell
# and the direnv hook in ~/.zshrc fires. The command is sent separately with
# send-keys. Passing the command to `tmux new-window` would run it under
# `sh -c`, where direnv never loads and no token would reach Claude.
#
# `maw token use <name>` still works as before — it edits the repo's .envrc,
# which is exactly what direnv then reads. Nothing here bypasses it.
set -e

LEICA=~/ghq/github.com/switchaphon/leica-oracle
POPSVET=~/ghq/github.com/switchaphon/pops-vet-oracle

DISCORD_ARGS='--channels plugin:discord@claude-plugins-official'

# Leica (main + discord window)
tmux new-session -d -s 01-leica    -n leica-oracle    -c "$LEICA"
tmux new-window  -t 01-leica       -n leica-discord   -c "$LEICA"

# Pops Vet
tmux new-session -d -s 05-pops-vet -n pops-vet-oracle -c "$POPSVET"

# DISCORD_STATE_DIR is set by each repo's .envrc, so it is not exported here.
tmux send-keys -t 01-leica:leica-oracle \
  'claude' Enter
tmux send-keys -t 01-leica:leica-discord \
  "claude $DISCORD_ARGS --dangerously-skip-permissions" Enter
tmux send-keys -t 05-pops-vet:pops-vet-oracle \
  'claude' Enter

# Attach
tmux attach -t 01-leica
