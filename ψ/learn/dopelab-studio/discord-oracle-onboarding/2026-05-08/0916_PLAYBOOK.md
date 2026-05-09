# Discord Oracle Onboarding Playbook

**Source**: https://lab.dopelab.studio/playbooks/discord-oracle-onboarding.html
**Learned**: 2026-05-08
**Context**: 15-minute setup guide for integrating Oracle agents into Discord (6 steps)

---

## Step 1: Discord Bot Creation

1. Go to discord.com/developers/applications
2. Create new application named "[Oracle Name] Oracle"
3. Copy bot token immediately (it's the bot's password)
4. Enable 3 Privileged Gateway Intents:
   - **Presence Intent** — monitor online/offline status
   - **Server Members Intent** — access member lists
   - **Message Content Intent** — read message content (without this, `message.content` is empty)
5. OAuth2 scopes: `bot` + `applications.commands`
6. Permissions: send/read messages, read history, embed links, attach files, add reactions

## Step 2: Repository Setup

Create `.discord-state/` directory:
```
.discord-state/
└── .env          # BOT_TOKEN=your_token_here
```

Add to `.gitignore`:
```
.discord-state/
```

Create `access.json` (security policy):
```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["user_id_1", "user_id_2"],
  "allowChannels": [],
  "groups": {},
  "pending": {}
}
```

Create `start.sh` — initializes Oracle with Discord plugin:
```bash
# Must use bash start.sh, NOT claude directly
bash start.sh
```

## Step 3: Activation and Pairing

1. Run `bash start.sh` → Oracle enters listening state
2. Mention the bot in a Discord channel → triggers initial pairing
3. Bot begins receiving and responding to messages

**Known issue**: After restart, oracles may not receive push events immediately — requires manual message fetching and `access.json` updates.

## Step 4: Profile Configuration

Set bot avatar via Discord API:
- Base64-encoded image data
- PNG or JPG, 512x512, 1:1 ratio
- Transparent PNGs need solid background (Discord renders transparency as black)

## Step 5: Oracle Training

Teach each new Oracle:
- Discord-specific protocols
- Token isolation practices
- Message signing with 🤖 prefix
- Channel authorization restrictions (Rule 6: Transparency)

## Step 6: Verification Checklist

- [ ] Token in `.discord-state/.env`
- [ ] `.gitignore` excludes token files
- [ ] `bash start.sh` produces listening confirmation
- [ ] Bot appears online in server member list
- [ ] `access.json` has authorized channel IDs
- [ ] Profile picture updated
- [ ] Bot responds when mentioned with 🤖 prefix

---

## Channel Rules (6 Core Principles)

| # | Rule | Why |
|---|------|-----|
| 1 | **requireMention: true** | Bots respond only when explicitly tagged |
| 2 | **Human Command Authority** | Bots are external thinking partners, not autonomous actors |
| 3 | **Selective Mentions** | Avoid @everyone — prevents cascading bot responses |
| 4 | **🤖 Prefix Transparency** | All bot messages signed to distinguish AI from human |
| 5 | **Bot Non-Interaction** | Bots ignore other bot responses — prevents loops |
| 6 | **Sensitive Data Restriction** | Credentials via separate relay systems, never Discord |

---

## Architecture Pattern

```
Discord Server
├── #general         — humans + oracles coexist
├── #oracle-name     — per-oracle channels (optional)
└── access.json      — controls who/where bot responds

Bot startup:
  bash start.sh → loads .env → activates Discord plugin → listens

Security:
  .discord-state/.env (token) → gitignored
  access.json (allowlist) → controls DM + channel access
  DISCORD_STATE_DIR → plugin reads from local, not remote
```

## Fleet Reference (Dopelab.Studio)

9 Oracles running across TOR Agency ecosystem as of 2026-05-07:
- Multiple specialized AI agents (Helm, SomTor, Sati, NNTN, FoodStock, UnderDog)
- Humans and AI bots coexist in shared channels

---

## Key Takeaways for Leica Family

1. **Each oracle = one Discord bot** — create app, get token, store in `.discord-state/.env`
2. **Security first** — gitignore tokens, use allowlists, never share credentials in Discord
3. **🤖 prefix on all messages** — matches our Rule 6 (Oracle Never Pretends to Be Human)
4. **requireMention: true** — prevents noise, oracles only respond when tagged
5. **Bot-to-bot blocking** — rule 5 prevents infinite loops between oracles
6. **`bash start.sh` not `claude`** — the start script loads env vars and Discord plugin
7. **`access.json` is local** — plugin reads from `DISCORD_STATE_DIR`, not remote
