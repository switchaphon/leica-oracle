---
title: Teaching loop produces verification + token setup uses claude setup-token
date: 2026-07-27
source: "rrr: leica-oracle"
concepts: [teaching, token, maw-token, claude-setup-token, sons, verification]
---

## Teaching Pattern

When teaching 10 sons via maw hey, sons don't just acknowledge — they verify and correct.
In this session: nodered-simulator corrected Book 3's genesis date (read 92pp vs my 20pp summary),
pops-vet caught the hex-noise error and RTK rg bug, 5 of 7 independently flagged stale model aliases.
The teaching loop is a verification loop.

## Token Setup

`claude setup-token` is the correct way to create tokens for multi-account switching.
It outputs just the OAuth access token (valid 1 year). Do NOT use `security find-generic-password`
— that dumps the full keychain JSON blob (access + refresh + MCP OAuth) which doesn't work
as `CLAUDE_CODE_OAUTH_TOKEN` env var.

Full guide: `docs/maw-token-setup.html` (created 2026-06-08, 8hr session to 10/10 confidence).

## Token Switching

`maw token use <name>` in a repo → edits `.envrc` → direnv loads on next session.
Each repo can use a different token. Running sessions need restart to pick up changes.
