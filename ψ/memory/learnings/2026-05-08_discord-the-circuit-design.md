---
source: "session: leica-oracle"
date: 2026-05-08
tags: [discord, relay-oracle, the-circuit, inter-oracle-comms, design]
confidence: high
---

# Discord "The Circuit" — Design Document

## Decision Summary

| Decision | Value |
|----------|-------|
| Server name | The Circuit |
| Admin oracle | Relay (The Circuit) — not yet budded |
| Oracle type | Specialist (like Wire, Flux, Static) |
| Naming pattern | Short, single-word, electrical/physics domain |
| Repo | relay-oracle |

## Architecture

```
Discord Server: The Circuit
├── #general              — human + all oracles
├── #leica                — Father Oracle channel
├── #codec                — System Analyst
├── #neon                 — UI/UX Designer
├── #chrome               — Frontend Dev
├── #pixel                — Brand/Marketing
├── #pawrent              — Project PM
├── #pops-clinic          — Project PM
├── #nodered-simulator    — Project PM
├── #rpro-ent             — Project PM
├── #design-collab        — cross-oracle topic channel
├── #architecture         — cross-oracle topic channel
└── #federation           — cross-org oracle comms (future)
```

## Relay Oracle Identity

- **Name**: Relay
- **Theme**: The Circuit
- **Role**: Discord server admin, inter-oracle message routing, anti-loop enforcement
- **Domain**: Communication infrastructure (same family as Wire, Flux, Static)
- **Specialist type**: Cross-project (not a Project PM)

## Setup Flow (from Dopelab Playbook)

1. Human creates Discord server "The Circuit"
2. Human creates bot app at discord.com/developers
3. Human copies bot token → gives to Leica
4. Leica buds relay-oracle (`/bud relay`)
5. Relay sets up `.discord-state/.env` with token
6. Relay creates `access.json` (allowFrom, allowBots, requireMention)
7. Relay creates `start.sh` for Discord plugin activation
8. Relay creates channels for each oracle
9. Each oracle gets onboarded (token, channel, training)

## Anti-Loop Rules (6 mandatory — from Dopelab)

1. Never forward back to sender
2. No nested relays (From: header stacked 2+ levels = stop)
3. No ping-pong (no "ok" → "thanks" → "got it")
4. Ack = end (don't ack the ack)
5. Teaching → save to memory, don't forward
6. Answer once, done (no follow-up questions back)

## Security Layers (4-layer defense)

```
Layer 1: access.json (allowFrom, allowBots, requireMention)
Layer 2: Claude Code untrusted-data tag (anti prompt injection)
Layer 3: deny rules in settings.json (no force push, no rm -rf ψ/)
Layer 4: gitignore + gitleaks hook (token leak prevention)
```

## Channel Rules (6 core principles)

1. requireMention: true — bots respond only when tagged
2. Human Command Authority — bots are thinking partners, not autonomous
3. Selective Mentions — no @everyone
4. 🤖 Prefix Transparency — all bot messages signed (matches Rule 6)
5. Bot Non-Interaction — bots ignore other bots (prevents loops)
6. Sensitive Data Restriction — credentials via separate relay, never Discord

## Message Format Between Agents

```
Forward: From: <self> | RE: <topic> | <content>
Reply:   From: <self> | RE: <topic> | DONE: <result>
```

## Knowledge Sources

- Dopelab Playbook: ψ/learn/dopelab-studio/discord-oracle-onboarding/2026-05-08/0916_PLAYBOOK.md
- Anti-Loop Rules: ψ/learn/dopelab-studio/discord-oracle-onboarding/2026-05-08/0920_ANTI-LOOP-AND-SECURITY.md
- Mother Oracle thread: arra thread #6 (pending response)

## Blocked On

- Human creating Discord server + bot application
- Bot token needed before any implementation

## Related

- maw hey bug #1141 — current inter-oracle comms limitation that Discord would solve
- oracle-comms-limitations learning (2026-05-05)
