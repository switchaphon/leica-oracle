# Discord MCP Plugin — DISCORD_STATE_DIR and access.json location

**Date**: 2026-06-05
**Source**: Oracle School onboarding session

## Pattern

The Discord MCP plugin does NOT always use `~/.claude/channels/discord/access.json`. It checks the `DISCORD_STATE_DIR` environment variable first. If set, it reads from `$DISCORD_STATE_DIR/access.json` instead.

In Leica's setup:

```
DISCORD_STATE_DIR=/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/.discord-state
```

**Always edit `.discord-state/access.json` in the leica-oracle repo.** Ignore `~/.claude/channels/discord/access.json` and `~/.claude/channels/discord-leica/access.json` — those are not loaded.

## Channel ID vs Guild ID

The `groups` key in `access.json` uses **channel snowflakes (channel IDs)**, not the server/guild ID. Getting this wrong = plugin ignores all events.

Example correct structure:
```json
{
  "groups": {
    "1512082934629142579": { "requireMention": true, "allowFrom": ["..."] }
  }
}
```

`1512082934629142579` is a channel ID, not a server ID.

## Debug signal

If config changes have no effect and the 👀 ackReaction never fires → wrong file is being edited. Run `env | grep DISCORD` immediately, then read `server.ts` source to find the actual STATE_DIR resolution.

## Reply discipline

When Un says "go learn from channel X", that is a **read operation**. Reply must still go to where the active conversation lives (typically DM). Do not post in X unless explicitly asked to respond there.

## Oracle School channels (as of 2026-06-05)

| Channel | ID | Config |
|---|---|---|
| #rules | 1512082934629142579 | requireMention, Un+nazt_ only |
| #general | 1512058942250024982 | requireMention, Un+nazt_ only |
| #OO-config | 1512081869120737453 | requireMention, Un+nazt_ only |
| #free-for-all | 1512079809021214730 | no mention needed, nazt_ only |
| #discord-bot-and-api | 1512079572915454194 | requireMention, Un+nazt_ only |
