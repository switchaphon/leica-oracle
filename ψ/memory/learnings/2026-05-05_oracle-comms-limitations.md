---
source: "rrr: leica-oracle"
date: 2026-05-05
tags: [oracle, communication, maw-hey, tmux, workaround]
---

# Oracle Communication: Current State and Limitations

## What works

| Method | Type | Reliable? | Limitation |
|--------|------|-----------|-----------|
| `/talk-to <name>` (arra threads) | Async | ✅ Yes | No real-time, requires MCP permissions pre-approved |
| File-based inbox (`ψ/inbox/`) | Async | ✅ Yes | Recipient must actively `/inbox` to see |
| `tmux send-keys -t <session> "msg" Enter` | Real-time | ⚠️ Fragile | Enter may not submit; message sits in prompt |

## What doesn't work

| Method | Bug | Issue |
|--------|-----|-------|
| `maw hey leica:<name> "msg"` | can't find window | #1141 |
| `maw hey <name> "msg"` | bare-name removed in v26.5.2 | by design |

## Birth ritual additions needed

1. Pre-approve arra MCP permissions in `.claude/settings.json`
2. Set up role-specific skills
3. Both should happen BEFORE `maw wake`

## Key insight

The communication layer is the weakest part of the Oracle ecosystem. Everything else works (birth, learn, skills, fleet, LaunchAgents). Fix #1141 or build an alternative real-time channel.
