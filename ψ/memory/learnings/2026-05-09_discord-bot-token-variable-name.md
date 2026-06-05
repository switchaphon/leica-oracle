---
source: "session: leica-oracle, Discord The Circuit setup"
date: 2026-05-09
tags: [discord, plugin, token, debugging, infrastructure, bulk-deploy]
confidence: high
---

# Discord Bot Token — Variable Name and Global Fallback

## The Bug

Discord plugin reads `DISCORD_BOT_TOKEN` from `.env`, NOT `BOT_TOKEN`. Using the wrong variable name causes silent fallback to `~/.claude/channels/discord/.env` — every bot connects as the same identity.

## Root Cause Chain

1. We wrote `BOT_TOKEN=xxx` in each oracle's `.discord-state/.env`
2. Plugin ignored it (wrong variable name)
3. Plugin fell back to `~/.claude/channels/discord/.env` which had Relay's token
4. ALL oracle bots connected as Relay → same messages delivered to all sessions

## The Fix

1. Use `DISCORD_BOT_TOKEN=xxx` (not `BOT_TOKEN`)
2. Remove `~/.claude/channels/discord/.env` global fallback
3. Each oracle has isolated `.discord-state/.env` with its own token

## Meta-Lesson

Test ONE instance end-to-end before bulk-deploying to 10. File existence verification is not functionality verification.
