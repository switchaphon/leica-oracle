---
title: Discord MCP plugin uses DISCORD_STATE_DIR env var to determine which access.json
tags: [discord, mcp-plugin, access.json, DISCORD_STATE_DIR, channel-id, debugging, config-location]
created: 2026-06-05
source: rrr: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Discord MCP plugin uses DISCORD_STATE_DIR env var to determine which access.json

Discord MCP plugin uses DISCORD_STATE_DIR env var to determine which access.json to read. If set, plugin reads $DISCORD_STATE_DIR/access.json — NOT the default ~/.claude/channels/discord/access.json. In Leica's setup: DISCORD_STATE_DIR points to .discord-state/ inside leica-oracle repo. Always edit that file. Groups keys must be channel IDs (snowflakes), not server/guild IDs. Debug signal: if ackReaction never fires despite edits, you're editing the wrong file — run env | grep DISCORD immediately.

---
*Added via Oracle Learn*
