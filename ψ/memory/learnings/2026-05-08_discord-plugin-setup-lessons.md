---
source: "session: leica-oracle, Discord setup"
date: 2026-05-08
tags: [discord, plugin, debugging, intents, relay, infrastructure]
confidence: high
---

# Discord Plugin Setup — Hard-Won Lessons

## 1. Privileged Intents Are Mandatory
Discord bots using discord.js MUST have all 3 Privileged Gateway Intents enabled in Developer Portal:
- Presence Intent
- Server Members Intent
- Message Content Intent

Without ALL enabled → `GatewayCloseCodes.DisallowedIntents` → silent crash. Even if code only uses MessageContent.

## 2. Test the Service Directly First
Standalone discord.js test script found the Intents error in 3 seconds. MCP infrastructure debugging found nothing in 90 minutes. Always test the actual service before debugging the wrapper.

## 3. start.sh Must Run From Shell
`exec claude --channels` replaces the process. Running `bash start.sh` as a prompt INSIDE Claude just sends the text as input. Must `/exit` first, then run from bare shell.

## 4. Auto Mode Blocks MCP Tools
Discord reply/react/edit tools are blocked by Claude Code's auto mode classifier by default. Fix: add explicit permissions in `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["mcp__plugin_discord_discord__reply", ...]
  }
}
```

## 5. access.json Format
Guild channels use `groups` (keyed by channel snowflake), NOT `allowChannels`:
```json
{
  "groups": {
    "CHANNEL_ID": { "requireMention": true, "allowFrom": [] }
  }
}
```

## 6. Token Location
Plugin reads from `DISCORD_STATE_DIR/.env` or `~/.claude/channels/discord/.env`. Shell env vars take precedence.
