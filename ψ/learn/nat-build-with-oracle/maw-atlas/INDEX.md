# maw-atlas Learning Index

## Overview

maw-atlas is a Discord fleet infrastructure plugin for maw-js. It manages Discord for the Oracle fleet — bots, tokens, channels, guilds, permissions, and message history.

**Key docs**:
- `2026-06-07/1405_QUICK-REFERENCE.md` — Comprehensive command reference, setup, patterns, troubleshooting

---

## Quick Links

| Topic | Document | Summary |
|-------|----------|---------|
| Everything | [2026-06-07/1405_QUICK-REFERENCE.md](2026-06-07/1405_QUICK-REFERENCE.md) | 758 lines: installation, all commands, token setup, channel management, watch/route, spawn-session, privileged intents, auto-mode behavior, patterns, diagnostics |

---

## Key Sections (Quick Reference)

### Installation
- Plugin system: `maw plugin install nat-build-with-oracle/maw-atlas`
- Manual: clone to `~/.maw/plugins/maw-atlas`

### Core Commands
```bash
maw atlas ls                          # list guilds + channels
maw atlas read <channel-id>          # read messages
maw atlas backfill [--all]           # backfill message history
maw atlas add-guild <invite-or-id>   # discover guild channels
maw atlas whoami                     # bot identity
maw atlas check                      # consolidation check
maw atlas wake <bot>                 # remote bot wake
maw atlas vesicle <bot>              # tmux transport demo
```

### Token Setup
- Pass (recommended): `pass insert discord/atlas-oracle-token`
- Env var: `export DISCORD_BOT_TOKEN=<token>`
- Custom dir: `export DISCORD_STATE_DIR=/path/to/.discord-state`

### Critical Concepts

1. **One Channel Per Oracle** — No shared channels between oracles (prevents double-replies)
2. **access.json** — Each oracle's `~/.discord-state/access.json` defines channels + permissions
3. **Privileged Intents** — Must enable Presence, Server Members, Message Content in Discord Developer Portal
4. **Channel Split Orchestration** — 5-step process to create new channels: preflight → discover → create → update access.json → restart bot
5. **Watch and Route** — Federation router automatically directs messages from Discord channels to oracle tmux windows
6. **Spawn-Session** — Complete workflow: bud → create channels → write access.json → store token → awaken with `--channels` flag
7. **Auto-mode Classifier** — May block Discord operations; declare intent before acting

---

## Learning Path

1. **Start here**: Read [1405_QUICK-REFERENCE.md](2026-06-07/1405_QUICK-REFERENCE.md) — covers all 9 major sections
2. **Hands-on**: Follow spawn-session workflow to create your first atlas oracle
3. **Deep dive**: Review "Privileged Intents" and "Channel Split Orchestration" sections
4. **Diagnostics**: Use `maw atlas check` and `maw atlas ls` for daily operations
5. **Troubleshooting**: See "Common Issues and Solutions" section in quick reference

---

## Related Context

From leica-oracle memories:
- `2026-05-10_discord-channel-split-orchestration.md` — Detailed validation of channel split pattern
- `2026-05-08_discord-plugin-setup-lessons.md` — Hard-won lessons (intents, test-first, token location, permissions)
- `2026-05-08_discord-the-circuit-design.md` — Original Discord architecture design for oracle fleet

---

**Version**: maw v26.6.6-alpha.1652, maw-atlas latest  
**Last updated**: 2026-06-07  
**Confidence**: High (validated against live fleet with 6+ oracles, 14+ channels)
