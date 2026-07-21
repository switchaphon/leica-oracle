---
title: Discord plugin reads `DISCORD_BOT_TOKEN` from `.env`, NOT `BOT_TOKEN`. Wrong var
tags: [discord, plugin, token, debugging, infrastructure, bulk-deploy]
created: 2026-05-10
source: rrr: leica-oracle — Discord The Circuit goes live
project: github.com/switchaphon/leica-oracle
---

# Discord plugin reads `DISCORD_BOT_TOKEN` from `.env`, NOT `BOT_TOKEN`. Wrong var

Discord plugin reads `DISCORD_BOT_TOKEN` from `.env`, NOT `BOT_TOKEN`. Wrong variable name causes silent fallback to global `~/.claude/channels/discord/.env` — all bots connect as same identity. Fix: use correct var name + remove global fallback. Meta-lesson: test ONE instance end-to-end before bulk-deploying to many.

---
*Added via Oracle Learn*
