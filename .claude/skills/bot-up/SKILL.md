---
name: bot-up
description: Bring an Oracle's Discord bot up in a tmux window — creates the window, verifies direnv supplied both tokens, launches claude with the discord channel, and confirms it attached. Use when the user says "bot up", "start the bot", "resume the discord bot", "เปิดบอท", "start leica bot", or names an oracle whose Discord bot is down. Do NOT use for Discord channel access/pairing (that is /discord:access).
---

# /bot-up — resume an Oracle's Discord bot

## Usage

```bash
bash ~/.claude/skills/bot-up/bot-up.sh <oracle> [session] [--no-bypass] [--force]
```

| arg | meaning |
|---|---|
| `<oracle>` | short name — `leica`, `pops-vet`, `chrome`, … (no `-oracle` suffix) |
| `[session]` | tmux session to put the window in. Omitted → finds one ending in the oracle's name (e.g. `09-leica`), or creates one |
| `--no-bypass` | drop `--dangerously-skip-permissions` (on by default; bots run unattended) |
| `--force` | replace an existing `<oracle>-discord` window instead of refusing |

Examples:

```bash
bash ~/.claude/skills/bot-up/bot-up.sh leica
bash ~/.claude/skills/bot-up/bot-up.sh pops-vet 04-pops-vet
bash ~/.claude/skills/bot-up/bot-up.sh chrome --force
```

## What it does

1. **Preflight** — repo exists, `pass show discord/<oracle>` resolves, `.envrc` has a
   `DISCORD_BOT_TOKEN` line, direnv is allowed. Fails before touching tmux.
2. **Refuses to double-launch** — two bots on one token reply twice to every message.
   `--force` replaces.
3. **Creates the window with no command**, so tmux starts an *interactive* shell and the
   direnv hook fires.
4. **Verifies before launching** — prints `discord=<len> claude=<len> token=<name>`.
   Lengths and a name only, never values.
5. **Launches** `claude --channels plugin:discord@claude-plugins-official`.
6. **Waits for the channel banner** and reports, or dumps the last 8 lines on failure.

## Why a script instead of three tmux commands

`tmux send-keys` only **types** unless the literal word `Enter` is passed as a separate
argument. Drop it and nothing runs; send a second command and the two **concatenate on one
input line** and execute as garbage. This bit us on 2026-08-05. The script's `send()`
helper always appends `Enter`, and clears the line with `C-u` first.

The window must be created with **no command**. `tmux new-window -c dir 'claude …'` runs it
under `sh -c`, where direnv never loads and no token reaches Claude.

## Rules this encodes

- **Never `source` a credential file to launch a bot.** `set -a; source .env` assigns
  unconditionally and overrides direnv's fresh value — it resurrects rotated tokens.
  Tokens come from `.envrc` → `pass`, nothing else.
- **Per-repo token separation is deliberate** (leica/pops-pet/pops-vet/vets-hub = `trio`,
  chrome/codec/neon/relay/rpro-ent = `un`, nodered = `tul`, rpro-saas = `kla`). The script
  never exports one repo's token into another's pane, and aborts if
  `CLAUDE_CODE_OAUTH_TOKEN` is empty rather than letting Claude fall back to its stored
  login.
- **Report only what is not derived from the secret's characters** — length, a boolean, or
  what the issuer answered.
- **Loaded ≠ accepted.** Every check here passes identically with a rotated token. Only a
  reply in Discord proves the credential is live, so the script says so at the end.

## Oracles without a bot

`pops-atlas` and `rpro-ent-atlas` have no `pass` entry — their bot applications were
deleted 2026-07-29. The script exits with that reason rather than a confusing failure.

## Related

- `<oracle>-oracle/start.sh` — the standalone launcher, same token rules, no tmux
- `/discord:access` — channel access and pairing, a different concern
