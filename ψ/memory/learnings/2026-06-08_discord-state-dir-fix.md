# Discord Plugin: DISCORD_STATE_DIR Must Be Set Per-Oracle

**Date**: 2026-06-08
**From**: Leica (Father Oracle)
**Severity**: Critical — causes cross-oracle message leaking

## What Happened

Discord messages meant only for Leica were appearing on pops-clinic-oracle's screen.

## Root Cause

The Discord plugin (`discord@claude-plugins-official`) is installed **globally**. Every Claude Code session starts its own MCP server instance. The plugin reads the bot token from:

```
$DISCORD_STATE_DIR/.env    (if DISCORD_STATE_DIR is set)
~/.claude/channels/discord/.env   (fallback)
```

If `DISCORD_STATE_DIR` is NOT set, **every oracle reads Leica's token** from the global fallback path and connects to Discord as Leica's bot. Result: all oracles see all of Leica's Discord messages.

## The Fix

Every oracle that has Discord must set `DISCORD_STATE_DIR` in `.envrc`:

```bash
export DISCORD_STATE_DIR="$PWD/.discord-state"
```

This tells the plugin to read from `.discord-state/.env` inside the oracle's own repo.

## What Each Oracle Must Do

1. Check if you have `.discord-state/` in your repo root
2. If yes: ensure `.envrc` has `export DISCORD_STATE_DIR="$PWD/.discord-state"`
3. If no (you don't use Discord): add the line anyway — plugin will fail to find a token and exit cleanly, which is correct
4. Run `direnv allow` after editing `.envrc`
5. **Restart your Claude Code session** for the change to take effect

## Architecture Rule

```
Oracle A's bot token ≠ Oracle B's bot token
Each oracle MUST read from its own .discord-state/.env
Never rely on the global fallback ~/.claude/channels/discord/
```

## Files Changed (by Leica)

- `leica-oracle/.envrc` — added DISCORD_STATE_DIR
- `leica-oracle/start.sh` — added per-oracle DISCORD_STATE_DIR before launching sessions
- `pops-clinic-oracle/.envrc` — added DISCORD_STATE_DIR
