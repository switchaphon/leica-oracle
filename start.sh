#!/bin/bash
cd /Users/switchaphon/ghq/github.com/switchaphon/leica-oracle
[ -f .env ] && { set -a; source .env; set +a; }
[ -f .discord-state/.env ] && { set -a; source .discord-state/.env; set +a; }
export DISCORD_STATE_DIR="$(pwd)/.discord-state"
exec claude --channels plugin:discord@claude-plugins-official
