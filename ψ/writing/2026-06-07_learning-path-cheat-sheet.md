# Leica Learning Path สูตรโกง

> 2 วัน (6-7 มิ.ย. 2026) — Discord boot fix, fleet update, deep learn 6 repos + 2 articles + 1 gist

---

## 🔧 Discord Plugin Boot Fix

### Token + State Directory

```bash
# Canonical location: leica-oracle/.discord-state/
ls /Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/.discord-state/
# .env (DISCORD_BOT_TOKEN=MTIz...) + access.json

# Symlink fallback path → canonical
ln -sf /Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/.discord-state \
  ~/.claude/channels/discord

# Env var in settings.json
"DISCORD_STATE_DIR": "/Users/switchaphon/ghq/github.com/switchaphon/leica-oracle/.discord-state"

# Reconnect plugin without restart
/mcp
```

### Channel Config (access.json)

```bash
# เพิ่มช่อง
# requireMention: false = ฟังทุกข้อความ, true = ต้อง @mention
# allowFrom: [] = ทุกคน, ["id1","id2"] = เฉพาะ
cat .discord-state/access.json
```

## 🚀 Fleet Boot (หลัง reboot)

```bash
~/ghq/github.com/switchaphon/leica-oracle/start.sh
```

### หรือ manual:

```bash
# Leica (main + discord)
tmux new-session -d -s 01-leica -n leica-oracle -c ~/ghq/github.com/switchaphon/leica-oracle
tmux new-window  -t 01-leica   -n leica-discord -c ~/ghq/github.com/switchaphon/leica-oracle

# Pops Clinic
tmux new-session -d -s 05-pops-clinic -n pops-clinic-oracle -c ~/ghq/github.com/switchaphon/pops-clinic-oracle

# Launch Claude Code
tmux send-keys -t 01-leica:leica-oracle    'claude' Enter
tmux send-keys -t 01-leica:leica-discord    'claude' Enter
tmux send-keys -t 05-pops-clinic:pops-clinic-oracle 'claude' Enter

# Attach
tmux attach -t 01-leica
```

### Opus 4.6 1M + Discord (P'Nat's recipe):

```bash
ANTHROPIC_MODEL=claude-opus-4-6[1m] command claude \
  --dangerously-skip-permissions \
  --channels plugin:discord@claude-plugins-official \
  --continue
```

## 📦 Update Tools

```bash
# maw-js (bun, from GitHub)
bun i -g maw-js@github:Soul-Brews-Studio/maw-js
maw --version

# arra-oracle-v3 (git pull)
cd ~/ghq/github.com/Soul-Brews-Studio/arra-oracle-v3 && git pull

# arra-oracle-skills-cli (bun, force refresh)
bun remove -g arra-oracle-skills
bun i -g arra-oracle-skills@github:Soul-Brews-Studio/arra-oracle-skills-cli#main
arra-oracle-skills --version

# Rollback maw ถ้าแตก
bun i -g maw-js@github:Soul-Brews-Studio/maw-js#47f1e69
```

## 📚 /learn — Deep Dive Repos

```bash
# Standard (3 agents)
/learn https://github.com/Soul-Brews-Studio/voice-bot
/learn https://github.com/Yeachan-Heo/oh-my-codex
/learn https://github.com/obra/superpowers
/learn https://github.com/JuliusBrussee/caveman

# Deep (5 agents)
/learn --deep https://github.com/nat-build-with-oracle/maw-atlas

# Gist (fetch + save)
gh gist view <gist-id> --raw > ψ/learn/path/file.md

# Blog article (WebFetch + save)
# ใช้ WebFetch tool แล้ว Write ลง ψ/learn/articles/
```

### Learn docs location:

```
ψ/learn/
├── Soul-Brews-Studio/voice-bot/       # Discord voice transcriber + AI
├── Yeachan-Heo/oh-my-codex/           # Codex CLI orchestration layer
├── obra/superpowers/                   # Claude Code skill plugin (14 skills)
├── JuliusBrussee/caveman/             # Token compression (~75%)
├── nat-build-with-oracle/maw-atlas/   # Discord fleet infrastructure
├── nazt/gists/                         # Nat's gists (maw token dig + more)
└── articles/                           # Blog posts + cheatsheets
```

## 📨 /talk-to — Broadcast to All Oracles

```bash
# List channels
/talk-to --list

# Send to all (manual — loop each thread)
/talk-to neon "message"
/talk-to pops-clinic "message"
/talk-to codec "message"
# ... etc
```

## 🔐 Discord Identity

```
Un (owner):  976696695528247296  switchaphon
Nat (master): 691531480689541170  nazt_
→ ONLY respond to these 2 IDs
```

## ⚡ ลัด

| ทำอะไร | คำสั่ง |
|--------|--------|
| boot fleet | `~/ghq/.../leica-oracle/start.sh` |
| reconnect Discord | `/mcp` |
| update maw | `bun i -g maw-js@github:Soul-Brews-Studio/maw-js` |
| update arra | `cd arra-oracle-v3 && git pull` |
| update skills-cli | `bun remove -g arra-oracle-skills && bun i -g ...#main` |
| learn repo | `/learn <url>` |
| learn deep | `/learn --deep <url>` |
| teach all oracles | `/talk-to` ทุก channel |
| cheatsheet | `/oracle-cheatsheet` |
| fleet status | `maw ls` |
| fleet doctor | `maw fleet doctor` |

## ⚠️ trap ที่เจอจริง

| trap | วิธีเลี่ยง |
|------|-----------|
| Discord plugin -32000 | token ไม่เจอ → symlink + DISCORD_STATE_DIR |
| `~/.claude/channels/discord/` มี access.json เก่า | ลบแล้ว symlink ไป .discord-state/ |
| `npm i -g maw-js` → 404 | maw ติดตั้งผ่าน bun จาก GitHub ไม่ใช่ npm |
| `bun i -g` ไม่ดึง version ใหม่ | `bun remove -g` ก่อน แล้ว `bun i -g ...#main` |
| `maw fleet adopt` → unknown command | v26.6 เปลี่ยนเป็น `maw fleet sync-windows` |
| `maw ls` บอก [orphan] | ปกติ — แค่ไม่ได้เปิดผ่าน `maw wake` |
| โพสต์ repo ของน้องทุกตัว | ตอบแค่ของตัวเอง ห้ามเปิดเผยของคนอื่น |
| Discord ใช้ markdown table | ไม่ render — ใช้ code block แทน |

---

🤖 Leica 🐱 — Father Oracle ของ Un | leica-oracle | 2026-06-07
