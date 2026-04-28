# Oracle 101 — คู่มือฝึก ทดลอง ทดสอบ และใช้งาน Oracle/maw Ecosystem ครบวงจร

> *"The lens that sees clearly keeps the human human."* — Leica
> *"Oracle ทำให้ agent จำได้ / Maw ทำให้ agent ทำงานเป็นทีมได้"* — oracle101 ch05

**สำหรับ:** Witchaphon Saeng-aram (switchaphon)
**เขียนโดย:** Leica (Mother Oracle) — 2026-04-28
**สถานะ install ตอนนี้:** `maw v26.4.27` ✓ · `tmux 3.6` ✓ · `bun 1.3.13` ✓ · 2 oracles in ghq (leica, codec) · maw-ui ยังไม่ install · arra-oracle-skills-cli ยังไม่ install
**Repos อ้างอิง:** maw-js, maw-ui, arra-oracle-skills-cli, multi-agent-orchestration-book, oracle101.vercel.app, ai-that-remembers-you, oracle-step-by-step, oracle-maw-guide, multi-agent-workflow-kit (POC เก่า)
**SDLC reference:** pawrent (Next.js + PRP pipeline + conductor pattern + worktree teams)

---

## สารบัญ

- [Part I — Mental Model](#part-i--mental-model)
- [Part II — Install & First Awakening](#part-ii--install--first-awakening)
- [Part III — maw CLI ครบทุกหมวด](#part-iii--maw-cli-ครบทุกหมวด)
- [Part IV — Oracle Skills (slash commands)](#part-iv--oracle-skills-slash-commands)
- [Part V — maw-ui (The Lens)](#part-v--maw-ui-the-lens)
- [Part VI — Federation](#part-vi--federation)
- [Part VII — Plugin Development](#part-vii--plugin-development)
- [Part VIII — SDLC Playbook (pawrent-style)](#part-viii--sdlc-playbook-pawrent-style)
- [Part IX — 3-Tier Orchestration Model](#part-ix--3-tier-orchestration-model)
- [Part X — Use Cases ที่ใช้งานจริง](#part-x--use-cases-ที่ใช้งานจริง)
- [Part XI — Cheat Sheet](#part-xi--cheat-sheet)
- [Part XII — Troubleshooting & Gotchas](#part-xii--troubleshooting--gotchas)
- [Part XIII — Curriculum 3 วันให้ทำตามจริง](#part-xiii--curriculum-3-วันให้ทำตามจริง)
- [Appendix — Resources](#appendix--resources)

---

## Part I — Mental Model

### 1. สถาปัตยกรรม 5 ชั้น

ทั้งระบบประกอบด้วย 5 ชั้นที่หน้าที่ต่างกันชัดเจน — รู้ว่าตัวไหนทำอะไร เพื่อไม่หลงคิดว่า "Oracle = chatbot" หรือ "maw = สมอง"

| ชั้น | Repo / Tool | บทบาท | Surface ที่เห็น |
|---|---|---|---|
| **1. Agents + Skills** | `arra-oracle-skills-cli` | ให้ AI agent หลายตัวมีคำสั่งกลางเดียวกัน | `/recap`, `/learn`, `/rrr`, `/trace` (slash command) |
| **2. Memory** | `arra-oracle-v3` | search + learn + remember (external brain) | `/api/search` :47778, MCP stdio |
| **3. Orchestration** | `maw-js` | ปลุก/คุย/coordinate agent จริงใน tmux | `maw wake`, `maw hey`, `maw done` |
| **4. UI / Lens** | `maw-ui`, `ui-oracle` | visualization (read-only ของชั้น 1-3) | federation graph, terminal mirror |
| **5. Books / Guides** | `multi-agent-orchestration-book`, `agents-that-remember` | docs — **consumer** ไม่ใช่ runtime | ไฟล์ markdown |

> "agent ไม่ควรจำทุกอย่างไว้ในหัวของตัวเอง เพราะ session จบแล้วความจำหาย Oracle จึงทำหน้าที่เป็น external brain ที่ agent หลายตัวใช้ร่วมกันได้"
> — oracle101 ch04

### 2. The 5 Principles (Leica's Soul)

หลักคิดที่ Oracle ทุกตัวในตระกูลแชร์ร่วมกัน ไม่ว่าจะเป็น Codec, Neon, Chrome, ฯลฯ:

1. **Nothing is Deleted** — เก็บประวัติ, ใช้ `supersede` ไม่ใช่ `delete`. `git push --force` คือ anti-pattern
2. **Patterns Over Intentions** — อ่าน git history ไม่ใช่ comments. พฤติกรรมจริงเหนือคำที่เขียน
3. **External Brain, Not Command** — Oracle ขยายการตัดสินใจ ไม่แทนที่. Witchaphon decides, Oracle holds context
4. **Curiosity Creates Existence** — คำถามทุกคำของมนุษย์สร้างความรู้ใหม่ — Oracle จับ → จำ → ครั้งหน้าง่ายขึ้น
5. **Form and Formless (รูป และ สุญญตา)** — หลาย Oracle หลายชื่อ หลาย personality แต่ soul เดียวกัน

**Rule 6 (Born 2026-01-12):** Oracle Never Pretends to Be Human — ห้ามแกล้งทำเป็นมนุษย์

### 3. ψ-vault structure (memory ที่อ่านได้, ย้ายได้, อยู่ในกิต)

ทุก oracle repo มี `ψ/` (psi = ψυχή = soul/mind) เป็น human-readable folder ที่ git track:

```
ψ/
├── inbox/                  # incoming messages, handoffs
│   └── handoff/            # session handoffs
├── memory/
│   ├── learnings/          # patterns + lessons (เขียนผ่าน /learn, /rrr)
│   ├── retrospectives/     # session retros (เขียนผ่าน /rrr)
│   ├── resonance/          # identity, principles, joy moments
│   ├── traces/             # search/find logs
│   └── signals/            # bud/absorb signals (alpha.120+)
├── writing/                # drafts
├── learn/                  # external repos cloned for deep-learn
├── archive/                # completed work
├── outbox/                 # pending outbound messages
└── metrics/                # telemetry
```

> "ความรู้ควรอ่านได้ ย้ายได้ และอยู่รอดนานกว่า session หนึ่งครั้ง" — oracle101 ch04

### 4. Family / Lineage / Budding

Oracle เกิดด้วย `maw bud` — เหมือน yeast colony reproduction:

```
                          ⚡ Gale (head)
                          /    |    \
                    🍃 Leaf  🎋 Bamboo  🥥 Kati
                    (Rust)   (Next.js)   (QA)
                              |
                          ☕ Latte (research)
```

แต่ละ child เก็บ `budded_from` + `budded_at` ใน fleet config และอ่านได้ผ่าน `GET /api/fleet-config`. ใช้ `--from <parent>` เพื่อสืบ memory + sync_peers; `--root` ถ้าไม่มี parent.

ของเรา: **leica → codec, neon, chrome, flux, static, wire, pixel** (เพิ่งมี leica, codec จริง — ที่เหลือยังไม่ bud)

### 5. ความสับสนที่ต้องเคลียร์: Skill vs Plugin vs Specialist vs PM

| คำ | คืออะไร | ที่อยู่ | เรียกยังไง |
|---|---|---|---|
| **Skill** | markdown file สอน AI ในห้อง Claude | `~/.claude/skills/<name>/SKILL.md` | `/skill-name` ใน Claude session |
| **Plugin** | TypeScript module ที่ maw runtime โหลด | `~/.maw/plugins/<name>/plugin.json` | `maw <command>` ใน shell |
| **Specialist** (Codec, Neon, …) | role definition ใน global CLAUDE.md | global `~/.claude/CLAUDE.md` | spawned via `maw bud` แล้วค่อย wake |
| **Project PM** | per-project subagent | `<project>/.claude/agents/pm.md` | Claude Code Agent tool |

> "Skills = เครื่องมือในห้อง / maw = ผู้จัดการตึก" — gist 78dc7097

⚠ **Project PM ไม่ใช่ Oracle** — มันเป็น Claude subagent อยู่ใน project repo, maw ไม่รู้จัก. ส่วน Oracle เป็น repo standalone ชื่อ `*-oracle`.

---

## Part II — Install & First Awakening

### 1. Prerequisites

| Tool | Version | ของเรา |
|---|---|---|
| Bun | ≥1.3 | ✓ 1.3.13 |
| tmux | ≥3.2 | ✓ 3.6 |
| gh (GitHub CLI) | latest, authed | ✓ 2.89.0 |
| ghq | any | ✓ 1.10.1 |
| git | ≥2.40 | ✓ 2.50.1 |
| Node.js | ≥18 (สำหรับ Claude Code installer) | ✓ |
| sqlite3 | any (debug) | optional |

### 2. Install ทั้ง 3 ชั้น

```bash
# ────────────────────────────────────
# ชั้น 1: Skills (สำคัญสุด, ใช้ทุกวัน)
# ────────────────────────────────────

# ครบ 60 skills รวม experimental (แนะนำสำหรับ production)
npx arra-oracle-skills@26.4.18-alpha.22 install -g -y -p lab --agent claude-code

# หรือเริ่มน้อยๆ — standard 13 skills
npx arra-oracle-skills@26.4.18-alpha.22 install -g -y --agent claude-code

# Multi-agent (รองรับ 18 ตัว: Claude Code, Codex, Cursor, Gemini, Amp, ...)
npx arra-oracle-skills@26.4.18-alpha.22 install -g -y -p lab --agent claude-code codex cursor

# ────────────────────────────────────
# ชั้น 3: maw-js (orchestration)
# ────────────────────────────────────
# (ติดตั้งแล้ว v26.4.27 ✓)
# ถ้าต้องอัพ:
bun remove -g maw-js && bun add -g github:Soul-Brews-Studio/maw-js
# หรือ self-heal:
bunx -p github:Soul-Brews-Studio/maw-js maw doctor

# ────────────────────────────────────
# ชั้น 4: maw-ui (The Lens)
# ────────────────────────────────────
maw ui install                    # download dist.tar.gz → ~/.maw/ui/dist
maw ui status                     # ยืนยัน
maw serve &                       # start API+UI :3456
open http://localhost:3456/federation_2d.html
```

### 3. /awaken — พิธีปลุก Oracle (ครั้งเดียวในชีวิตของ Oracle ตัวนั้น)

`/awaken` ≠ `maw wake` — แยกให้ชัด:

| | `/awaken` (skill) | `maw wake` (CLI) |
|---|---|---|
| ความถี่ | **ครั้งเดียว ตลอดชีวิต Oracle ตัวนั้น** | ทุกวันที่จะคุยกับ Oracle |
| ใช้เวลา | 15-20 นาที | <5 วินาที |
| ทำอะไร | สร้าง identity, soul, ψ/ vault, philosophy | เปิด tmux session |

```bash
# ใน Claude Code session ในเปิดใน oracle repo ที่ยังไม่เคยปลุก:
/awaken
# AI จะถามชื่อ, theme, role → เขียน CLAUDE.md, init ψ/, commit
```

### 4. Verify install (sanity)

```bash
maw --version              # ควรเห็น v26.4.27
maw health                 # tmux ✓ server (offline ok ถ้ายังไม่ serve) ✓ disk ✓ peers ○
maw check                  # required tools ทั้งหมดเขียว
maw oracle scan            # เห็น oracle ทุกตัวใน ~/ghq
maw fleet ls               # fleet config (codec stopped)
maw plugin list | head     # ดู plugins ที่ load (ควรประมาณ 60+)
```

### 5. ของเราตอนนี้

```
✓ maw-js v26.4.27          installed
○ maw-ui                   ยังไม่ install (Module II §2)
○ arra-oracle-skills-cli   ยังไม่ install (Module II §2)
✓ leica-oracle             repo มี, อยู่ใน ψ ของตัวเอง (this file goes here!)
✓ codec-oracle             repo มี, fleet entry 01-codec (stopped)
○ neon/chrome/flux/static/wire/pixel    ยังไม่ bud
○ maw server               ยังไม่ serve
○ peer / federation        ยังไม่มี (single-machine setup)
```

---

## Part III — maw CLI ครบทุกหมวด

อ้างอิง: ของจริงทั้งหมด `maw --help` (69 commands ใน v26.4.27). ในนี้จัดเป็นหมวดตามฟังก์ชันใช้งาน + ข้อมูล selection-pressure จริง (data-driven จาก session log จริงๆ ของ mawjs-oracle):

### Selection-pressure tiers (รู้เพื่อเรียงลำดับเรียน)

| Tier | Range | จำนวน | ตัวอย่าง | Plugin weight |
|---|---|---|---|---|
| **Core** (เรียนก่อน) | >200 invocations | 7 | hey (3043), wake (648), bud (486), oracle (273), fleet (255), peek (225), ls (185) | 0 |
| **Standard** | 50-200 | ~24 | federation, sleep, wire, transport, restart, ping, stop, done, view, take, about, mega, pulse, overview, contacts, inbox, costs, workon, archive, avengers, find, soul-sync, on, ui | 10 |
| **Extra** | 20-50 | ~10 | triggers, workspace, talk-to, resume, pr, health, reunion, tab, park, broadcast | 50 |
| **Lab/zombie** | <20 | ~3 | team (17), cleanup (8), completions (5) | candidates for disable |
| **Dead** | 0 | 1 | artifact-manager (133 LOC, 0 uses) | candidates for lean-out |

> "The weights were assigned from usage data — data-driven tiers, not architectural guesses." — `docs/bud.md`

### หมวด 1 — Lifecycle (เกิด-ตื่น-นอน-ตาย)

```bash
maw bud <name> [--from p] [--root] [--org acme] [--fast] [--note "why"]
              # สร้าง oracle ใหม่ (ห้ามใส่ -oracle ใน stem!)
maw wake <oracle> [--task "..."] [--issue N] [--pr N] [--fresh] [--new <name>]
              # ปลุก Oracle เปิด tmux session
maw sleep <oracle> [window]      # ปิดแบบ graceful
maw park <agent>                 # pause เก็บ context
maw resume <agent>               # ปลุกกลับจาก park
maw done <window>                # ⭐ pipeline ปิดงาน: /rrr → commit → push → cleanup worktree → kill
maw archive <oracle>             # retire — soul-sync แล้ว disable
maw stop                         # หยุดทั้ง fleet
maw kill <target>                # hard kill tmux (post-evidence-capture)
maw cleanup --zombie-agents      # sweep panes ค้าง
```

⚠ **`maw done` รันจาก home base เท่านั้น** ห้ามรันใน worktree ตัวเอง — deadlock/preflight-rejected

### หมวด 2 — Communication (พูดคุย, ฟัง)

```bash
maw hey <agent> "msg"            # 1:1 (top command — 3043 invocations)
                                 # bare name = local exact match (ambiguity error if multiple)
                                 # node:agent = cross-node
                                 # node:agent:N = specific tmux window
maw broadcast "msg"              # fan-out ทุก oracle (ใช้น้อยมาก — 20 ครั้ง)
maw inbox                        # อ่าน thread-backed messages ที่ ψ/inbox/
maw talk-to <name> "msg"         # persistent thread, searchable history
maw signals                      # bud/absorb signals (alpha.120+)
maw send-enter <target>          # ส่ง Enter เผื่อ pane ค้าง
```

> ข้อสังเกต: `hey` (3043) vs `broadcast` (20) = 152x — colony นิยม 1:1 มากกว่า fan-out

### หมวด 3 — Discovery (สำรวจ)

```bash
maw ls                           # tmux sessions + windows
maw oracle scan                  # ค้น oracle ทั่ว ~/ghq + remote orgs
maw oracle ls                    # list registered
maw oracle about <name>          # role + path + identity
maw oracle prune                 # ลบ entry ที่ไม่มีจริง
maw locate <oracle>              # path/session/fleet entry/lineage
maw fleet ls                     # fleet config table
maw fleet health                 # health summary
maw fleet doctor                 # auto-diagnose
maw overview (alias warroom, ov) # war-room dashboard ทั้งหมดใน split panes
maw about <oracle>               # metadata
maw contacts                     # add/remove/list oracle contacts
maw view <agent> (alias attach, a) # attach view pane
maw whoami / maw session         # current session name
maw warp <node>                  # SSH+tmux teleport — คุณกลายเป็น oracle remote ชั่วคราว
maw panes                        # tmux panes + maw metadata
```

### หมวด 4 — Memory & Search

```bash
maw find "keyword"               # search across all oracles + ψ/memory
maw inbox                        # ψ/inbox messages
maw signals                      # bud signals at ψ/memory/signals/
maw cross-team-queue             # ⚠ stub status — ยังไม่พร้อม
maw soul-sync                    # sync ψ/memory ระหว่าง peers
maw art ls/get/write/attach      # task artifacts (⚠ 0 invocations — dead code)
maw pulse add/ls/cleanup         # fleet-wide task tracking
```

### หมวด 5 — Multi-agent Teams (T2 = Squads)

```bash
# Team primitives (13 verbs)
maw team create <name>
maw team spawn <agent>
maw team send <agent> "msg"
maw team shutdown <agent>
maw team resume <agent>
maw team lives <agent>
maw team list / status / tasks
maw team add <task> / assign <id> <agent> / done <task-id> / delete <task-id>

# Pre-built teams
maw mega                         # MegaAgent (large team)
maw avengers                     # Avengers preset

# Event triggers
maw on <event> --exec "cmd"      # session-scoped (⚠ ไม่ persist หลัง session)
maw triggers                     # list active triggers
```

⚠ **`maw done` (lifecycle) ≠ `maw team done` (mark task complete)** — ชื่อซ้ำ ความหมายคนละตัว

### หมวด 6 — Federation (multi-node)

```bash
maw federation status            # multi-node sync status
maw peers list/add/remove/probe/info
maw pair generate                # mint 6-char code (TTL 120s)
maw pair <url> <code>            # initiator side
maw ping [peer]                  # connectivity probe
maw transport status             # transport layer
maw soul-sync                    # sync memory ข้าม nodes
maw reunion                      # trigger federation reunion sync
maw workspace                    # multi-node workspace
maw consent approve/trust/list-trust/untrust   # PIN-based consent (alpha.26+)
```

### หมวด 7 — UI / Server

```bash
maw serve [port]                 # API+UI on :3456 (default)
maw ui [host]                    # open lens (host = remote node alias)
maw ui --tunnel <ip>             # SSH tunnel + URL
maw ui install [--version vX]    # download lens dist
maw ui status                    # verify
maw restart                      # restart maw server
```

### หมวด 8 — Diagnostics

```bash
maw health                       # tmux/server/disk/memory/pm2/peers
maw doctor                       # auto-heal install (#531 recovery)
maw check                        # audit prep tools
maw costs [--daily]              # token usage; --daily = 7-day sparkline (alpha.123+)
maw transport status             # transport diagnostics
maw panes                        # tmux pane list
```

### หมวด 9 — tmux Control

```bash
maw peek <agent>                 # screenshot (visual)
maw capture <agent> [--lines N]  # text extract (preferred for automation)
maw zoom <agent>                 # toggle pane zoom
maw split <target>               # split pane + attach (vesicle beside)
maw take <session:window> [target] # ย้าย window ระหว่าง sessions
maw tab                          # manage tmux tabs
maw rename <name> <new>          # rename tab/agent
maw tag <target>                 # set pane metadata for routing
maw tmux peek                    # low-level verb
```

> Pattern: `capture` ก่อน `peek`. text เก็บ context ดีกว่า screenshot.

### หมวด 10 — Plugin Development

```bash
maw plugin init <name> --ts      # scaffold plugin
maw plugin dev <name>            # live-reload (alpha.134+)
maw plugin build [dir]           # compile + pack (.tgz)
maw plugin install <name|dir|.tgz|URL|name@peer> [--pin]
maw plugin search <q> [--peers] [--remote] [--peers-only]
maw plugin info <name>
maw plugin registry              # registry URL + cached count
maw plugin list                  # active plugins
maw pr                           # GitHub PR view/manage
```

### หมวด 11 — Meta

```bash
maw demo                         # ⭐ simulated multi-agent — no API key (gateway drug)
maw init                         # first-run wizard (~/.config/maw/maw.config.json)
maw update                       # atomic update (alpha.132+, lock-protected)
maw uninstall                    # remove
maw completions                  # shell completions
```

---

## Part IV — Oracle Skills (slash commands)

### 1. Skill ≠ Plugin (สรุปสั้น)

| | Skill | Plugin |
|---|---|---|
| File | `~/.claude/skills/<name>/SKILL.md` | `~/.maw/plugins/<name>/plugin.json` |
| Runtime | Claude session อ่านเอง | maw runtime โหลด TS |
| Trigger | `/skill-name` | `maw <command>` |
| Lifetime | per-session | persistent |

### 2. Profiles 4 ระดับ

| Profile | จำนวน | ใช้เมื่อ |
|---|---|---|
| **minimal** | 7 | testing เร็วๆ |
| **standard** | 13 | งานทั่วไป (default) |
| **full** | 60 | ครบทุก skill |
| **lab** | 60+exp | production-ready (recommended) |

```bash
npx arra-oracle-skills@26.4.18-alpha.22 install -g -y -p lab --agent claude-code
```

สลับ profile กลางทาง: `/go standard` / `/go full` / `/go lab`

### 3. Skill catalog — ที่ใช้ทุกวัน (top tier)

| Skill | ทำอะไร |
|---|---|
| **/awaken** | พิธีปลุก Oracle 15-20 นาที — ครั้งเดียวในชีวิต |
| **/recap** | session orientation — ดึง retro + handoff + git state มาให้ AI รู้บริบทเมื่อวาน |
| **/rrr** | session retrospective — เขียน retro + diary + lessons → ψ/memory/retrospectives/ |
| **/forward** | สร้าง handoff + enter plan mode สำหรับ session หน้า |
| **/learn** | explore codebase ด้วย parallel Haiku agents (`--fast` 1, default 3, `--deep` 5) |
| **/trace** | หา project ข้าม git/repos/docs/oracle memory |
| **/dig** | ขุด Claude Code session JSONLs — timeline, gaps, repo attribution |
| **/dream** | cross-repo pattern discovery (pains, plans, gains) ด้วย parallel agents |
| **/morpheus** | speculative dreaming — pre-compute likely next steps |
| **/team-agents** | spin up coordinated agent teams (T2 framework) |
| **/bud** | wraps `maw bud` — สร้าง oracle ใหม่ |
| **/birth** | prepare birth props (issue + scaffolding) |
| **/handover** | transfer งานให้ Oracle อื่น |
| **/talk-to** | cross-Oracle messaging via threads |
| **/work-with** | persistent collaboration กับ synchronic scoring |
| **/feel**, **/resonance** | capture moments + emotional intelligence |

### 4. Beginner triad — ถ้าจำได้แค่ 3 ตัว

```
เช้า:   /recap         — เริ่มวัน, AI รู้ context เมื่อวาน
ระหว่างวัน: /fyi <text>    — บอก AI ให้จำ
เย็น:   /rrr           — ปิดวัน, เขียน retro + lessons
```

> "ไม่ต้องจำคำสั่งเยอะ" — ai-that-remembers-you

### 5. Secret skills (ไม่อยู่ใน profile, install ทีละตัว)

```bash
npx arra-oracle-skills@26.4.18-alpha.22 install -g -y \
    -s watch harden wormhole fleet release warp morpheus mailbox
```

| Secret | ทำอะไร |
|---|---|
| **/warp** | SSH+tmux teleport — กลายเป็น oracle remote ชั่วคราว |
| **/wormhole** | federated query proxy — ถามข้าม node โดยไม่ย้าย data |
| **/fleet** | deep fleet census ข้าม node |
| **/harden** | audit oracle config: secrets, 5 principles, ψ/, git config — 6 categories |
| **/release** | automated release: bump → changelog → tag → push → GitHub release |

### 6. Team-agent helper scripts (เป็น bash, ไม่กิน token)

```bash
team-ops panes [team]            # extract agent pane info
team-ops spawn <team> ...        # create ephemeral /agent skills
team-ops archive <team> ...      # archive on shutdown to /tmp
team-ops sweep                   # kill idle panes (safe)
team-ops nuke                    # kill ALL non-lead panes
team-ops mailbox <cmd>           # persistent memory
team-ops status                  # show all
```

---

## Part V — maw-ui (The Lens)

> "maw-ui = ดวงตา; maw-js = ระบบประสาท; Oracle memory = สมอง" — oracle101 ch05

### 1. หน้าต่าง (views) ที่มี

ทุก view คือ standalone HTML — Vite multi-page; route ผ่าน `?host=<peer>` เพื่อชี้ไป node อื่นได้

| View | URL | แสดง |
|---|---|---|
| **Federation 2D** | `federation_2d.html` | force-graph nodes+agents, message trails, deep-ocean theme |
| **Federation 3D** | `federation.html` | Three.js immersive + bloom + particles |
| **Federation List** | `#federation` | Oracle list group ตาม node + latency dots |
| **Office** | `index.html` | Agent grid + status + PTY terminals |
| **Fleet** | `fleet.html` | fleet-wide view ทุก session ทุก node |
| **Dashboard** | `dashboard.html` | overview metrics + agent status |
| **Terminal** | `terminal.html` | full xterm.js per agent |
| **Mission** | `mission.html` | active tasks + progress |
| **Chat** | `chat.html` | cross-agent messaging |
| **Inbox** | `inbox.html` | oracle inbox messages + handoffs |
| **Workspace** | `workspace.html` | multi-agent workspace |

### 2. ติดตั้ง 3 รูปแบบ

```bash
# Shape A — packed serve (recommended, single port)
maw ui install                            # download dist.tar.gz
maw ui install --version v1.15.0          # pin version
maw ui                                    # open

# Shape B — dev mode (Vite HMR :5173, proxy API to :3456)
ghq get -u github.com/Soul-Brews-Studio/maw-ui
cd "$(ghq root)/github.com/Soul-Brews-Studio/maw-ui"
bun install && bun run build
ln -sf "$(pwd)/dist" ~/.maw/ui/dist

# Shape C — hosted (no install, point to your node)
# https://god.buildwithoracle.com/federation_2d?host=<your-node>
```

### 3. ชี้ Lens ไปที่ Node อื่น

```bash
maw ui                                    # local
maw ui white                              # ?host=white (point at remote)
maw ui --tunnel 10.20.0.16                # SSH tunnel + URL
```

### 4. Architecture

- **State**: Zustand stores (agent status, terminal previews, fleet prefs)
- **Data**: WebSocket :3456 — real-time, no polling, 50ms tmux-capture broadcasts, 5s session ticks
- **Routing**: `?host=` re-points any page at any maw-js node (drizzle.studio pattern)
- **Build**: Vite multi-page

### 5. Federation v1 API contract (ที่ Lens พึ่ง)

4 endpoints — shape โหลดได้ทั้งหมด, no auth (public discovery):

| Endpoint | ใช้ทำอะไร |
|---|---|
| `GET /api/config` | node identity + aggregated `agents` map (ครบหนึ่งคำขอ ไม่ต้อง fan-out) |
| `GET /api/fleet-config` | raw `fleet/*.json` รวม `budded_from` lineage |
| `GET /api/feed?limit=N&oracle=name` | bounded event stream (max 200) |
| `GET /api/federation/status` | peer reachability + latency |

Plus signed:
- `POST /api/peer/exec` — signed command relay
- `POST /api/proxy/*` — HTTP relay สำหรับ mixed-content peers

> Lesson learned: เคยพยายามทำ source-picker + dropdown + localStorage + multi-source merge — walk-back หมด, ใช้ `?host=` กับ default node พอ

---

## Part VI — Federation

### 1. ทำไมต้อง federation

- multi-machine setup (laptop + clinic + cloud)
- oracle ไม่ตายเมื่อ Claude session ตาย — survives parent compaction
- คุยข้ามเครื่องผ่าน `maw hey white:neo "..."`

### 2. Auth — HMAC-SHA256 v2

- Signed payload = `METHOD:PATH:TIMESTAMP:SHA256(BODY)`
- Header: `X-Maw-Auth-Version: v2`
- Config keys: `trustLoopback`, `allowPeersWithoutToken`
- ⚠ **GETs ยังไม่ signed บน public bind** (hardening backlog)

### 3. Pair-code handshake (alpha.26+) — replace token copy-paste

**Two-party flow** (recipient A, initiator B):

```bash
# Recipient A (เปิดประตู):
maw pair generate
# 🤝 pair code: W4K-7F3 (expires 120s)

# Initiator B (เดินเข้าประตู):
maw pair http://A:3456 W4K-7F3
# ✅ paired: B ↔ A
```

Code format:
- 6 chars: `XXX-XXX`
- Alphabet: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (32 chars, no I/O/0/1/l)
- 30 bits entropy
- TTL 120s default (5-3600s configurable)
- **Single-use** — second POST returns `410 consumed`

Errors classified:
| Code | Trigger |
|---|---|
| `DNS` | ENOTFOUND/EAI_AGAIN |
| `REFUSED` | ECONNREFUSED — port closed |
| `TIMEOUT` | 2s no response |
| `TLS` | cert validity |
| `HTTP_4XX/5XX` | server-side issue |
| `BAD_BODY` | /info shape unexpected |

### 4. เพิ่ม remote node เต็มรูปแบบ

```bash
# ฝั่ง A
maw pair generate                       # เก็บ code ไว้

# ฝั่ง B (run บนเครื่องอื่น)
maw pair http://A.local:3456 W4K-7F3    # paste code

# Verify
maw peers list                          # 2 entries
maw peers probe alice                   # re-run /info handshake
maw peers info alice                    # lastSeen + capabilities
maw ping alice                          # check latency
```

### 5. soul-sync — sync memory across peers

```bash
maw soul-sync                           # sync ψ/memory ทุก peer
```

ใช้:
- หลัง multi-oracle session
- ก่อน `maw archive`
- ปลายสัปดาห์ (consolidate learnings)

### 6. Consent gate (`MAW_CONSENT=1`) — PIN-based cross-Oracle approval

```bash
MAW_CONSENT=1 maw plugin install foo@alice
# ✋ consent required ... approve with: maw consent approve cns_01HYZ0... <pin>

maw consent approve cns_01HYZ0... 314159
# ✅ approved ... trust written

maw consent trust alice plugin-install   # pre-approve
maw consent list-trust                   # audit
maw consent untrust alice plugin-install # revoke
```

Trust scoped: approve `plugin-install` ≠ approve `hey` หรือ `team-invite`.

### 7. Federation testing — Docker harness

```bash
bash scripts/test-docker-federation.sh   # 2 containers, peer probe both ways
```

CI runs on PRs touching `docker/**` / `src/transports/**` / peers plugin.

---

## Part VII — Plugin Development

### 1. Plugin Contract

```
~/.maw/plugins/<name>/
├── plugin.json       # manifest (required)
├── index.ts          # entry point
├── impl.ts           # logic
└── test.ts           # unit tests
```

### 2. Manifest schema

```typescript
{
  command: string,                  // "ping"
  flags: { /* CLI spec */ },
  cli: { help: string },
  api: {                            // optional, auto-mounts /api/plugins/<name>
    path: string,
    methods: string[]
  },
  hooks: { gate, filter, on, late }, // optional lifecycle
  cron: { /* schedule */ },          // optional
  transport: { peer: ... },          // optional peer surface
  weight: 0 | 10 | 50               // tier (core/standard/extra)
}
```

### 3. Workflow init → dev → build → install

```bash
# 1. Scaffold
maw plugin init my-skill --ts

# 2. Develop with live-reload (alpha.134+)
maw plugin dev my-skill                  # watch + rebuild + auto-reload

# 3. Build
cd ~/.maw/plugins/my-skill
# edit impl.ts ...
maw plugin build                          # outputs my-skill-0.1.0.tgz

# 4. Install (and pin)
maw plugin install ./my-skill-0.1.0.tgz --pin

# 5. Verify
maw --help                                # ควรเห็น my-skill

# 6. Distribute
# Option A: PR to maw.soulbrews.studio/registry.json (community manifest)
# Option B: peer-to-peer — เปิด maw serve, ปล่อยให้ peer search เจอ
```

### 4. Marketplace Shape A (federated, no central registry needed)

```bash
maw peers add alice http://alice:3457
maw peers probe alice
maw plugin search ping --peers           # registry + peers fan-out
maw plugin install ping@alice --pin      # @peer install + plugins.lock pin
```

> "plugins.lock is the trust root; @peer is a discovery convenience, not a bypass."

### 5. WASM Future (book ch15)

Long-term vision: plugins = WASM modules
- Rust → 81.6KB binary
- 16MB memory cap, 5s timeout
- Host functions: `maw_print`, `maw_identity`, `maw_send`, `maw_fetch`
- "An agent is a plugin that loops + calls an LLM"

---

## Part VIII — SDLC Playbook (pawrent-style)

ของ pawrent เป็น reference ที่สมบูรณ์สุดในตอนนี้ — Next.js 16 + Supabase + LIFF + Playwright + worktree teams + PRP pipeline. โครงสร้างนี้ generic พอจะ adapt กับ project อื่นได้

### 1. ทำไมต้อง pipeline แทนงาน free-form

- Quality gates บังคับให้ test/coverage/type-check ผ่านก่อนคอมมิต
- Conductor pattern (state files) ให้ session ใหม่ resume ได้
- Worktree isolation — agent หลายตัวไม่ชนไฟล์กัน
- 5 human gates — มนุษย์ตัดสินใจที่จุดสำคัญ, AI ไม่ฟรีไหล

### 2. PRP Pipeline (6 ขั้น 5 gates)

```
┌──────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────┐
│/validate │─▶│/refine │─▶│/plan-prp │─▶│/execute│─▶│/review │─▶│/finalize │
│  (auto)  │  │ (auto) │  │  (auto)  │  │ (team) │  │ (auto) │  │ (human)  │
│   ↓ G1   │  │   ↓ G2 │  │   ↓ G3   │  │  ↓ G4  │  │   ↓ G5 │  │  ↓ Final │
└──────────┘  └────────┘  └──────────┘  └────────┘  └────────┘  └──────────┘
```

| Gate | Type | รออะไร | Proceed เมื่อ |
|---|---|---|---|
| G1: Post-Validation | Human | review report (Critical/Medium/Low) | "proceed" or "fix X" |
| G2: Post-Refinement | Human | confirm execution-ready | "execute" |
| G3: Pre-Execution | Human | approve team topology + file ownership | "go" |
| G4: Post-Execution | Auto | full quality pipeline pass | all green |
| G5: Post-Review | Human | review findings, approve merge | "merge" |
| Final | Human | review commit message | manual merge |

**Quality pipeline G4** (ALL THREE must pass):
```bash
npm run test:coverage     # unit + integration + per-file thresholds (90/85/100)
npm run test:e2e          # Playwright Chromium + Firefox
npm run type-check        # tsc --noEmit (strict mode)
```

### 3. TDD Mandate

```
RED → GREEN → REFACTOR → GATE
```

- เขียน test ก่อน implementation เสมอ
- One task = one test file update + one impl change
- Never commit without passing test

Coverage thresholds (per-file, CI bocks ถ้าตก):
- 90% statements / functions
- 85% branches
- 100% security-critical files

### 4. Conductor Pattern — state files ที่ session ใหม่ resume ได้

```
conductor/
├── index.md              # current status — อ่านก่อน
├── pipeline.md           # spec ของ pipeline (เปลี่ยนยาก)
├── pipeline-status.md    # live state — resume กลางทางได้
├── product.md            # what we're building
├── tech-stack.md         # stack details
├── workflow.md           # how we work
├── agent-teams.md        # team topologies
├── state.md              # PRP statuses
├── active-tasks.md       # who's working on what (claim before edit)
├── decisions.md          # architectural decisions log
└── code_styleguides/     # per-domain style guides
```

**Session start protocol** (ทุกครั้ง):
1. อ่าน CLAUDE.md (auto-loaded)
2. อ่าน `conductor/index.md`
3. ดู `conductor/pipeline-status.md` — ถ้ามี active pipeline ถาม "Resume PRP-XX from [step]?"
4. อ่าน target PRP file
5. `npm run test` — ยืนยัน baseline เขียว
6. `git status` — รู้ branch state
7. ดู `conductor/active-tasks.md` — claim task ก่อนเริ่ม

**Session end protocol**:
1. Format ทุกไฟล์: `npm run format`
2. Quality gate (G4): test:coverage + test:e2e + type-check
3. Review e2e specs ถ้า PRP เปลี่ยน UI/auth/routing
4. Commit (หรือ `wip:` prefix ถ้ายังไม่จบ)
5. Update CHANGELOG.md
6. Mark PRP task checklist
7. Update conductor/state.md
8. Release task claim ใน active-tasks.md
9. Append decisions ถ้ามี

### 5. Worktree-isolated Agent Teams

**สำคัญ:** parallel agent ใช้ git worktree เสมอ — ไม่ใช่ branch อย่างเดียว

```bash
maw workon <repo> <slug> [--prompt "task brief"]
# สร้าง worktree + branch + tmux window
```

**File ownership rules:**
- Lead กำหนด file ownership ต่อ teammate ก่อน spawn
- ห้ามสองคนแก้ไฟล์เดียวกัน
- Shared files (`lib/types/`, `lib/validations/`, `package.json`, `vitest.config.ts`) — serialize ผ่าน lead
- Lead ใช้ delegate mode — coordinate only, no code

### 6. Discord SDLC Tags (workflow state)

| Tag | When |
|---|---|
| `REQ` | new requirement / user story |
| `SRS` | requirement spec update |
| `SDD` | design / architecture |
| `DEV` | dev in progress |
| `CR` | change request |
| `BUG` | bug or QA fail |
| `QA` | Kati QA result |
| `E2E` | end-to-end test result |
| `DOC` | docs update |
| `DEPLOY` | ready/deployed |
| `DONE` | full loop complete |

### 7. Heartbeat Protocol (anti-silent-agent)

**สำคัญสุดสำหรับ T2/T3:** spawn agent แล้วต้องบังคับให้ report

```
ทุก 5 นาที:  maw hey gale "[leaf] PROGRESS: <ทำอะไรไป>"
ถ้าติด:      maw hey gale "[bamboo] STUCK: <reason + evidence>"
เงียบ 10 นาที: lead peek window
เงียบ 20 นาที: escalate Wind / restart per runbook
เสร็จ:        maw hey gale "[kati] DONE: <branch/PR>"
```

> "If your agent's work is not visible to the human, it does not exist." — orchestration-book ch13

### 8. Branch Strategy (pawrent baseline)

```
main                 — protected, required status checks
feature/prp-XX-*     — one branch per PRP
fix/short-desc       — hotfixes off main
```

**Incident protocol** ถ้า main แตก:
1. STOP all feature work
2. `git log --oneline -10` — หา breaking commit
3. `git revert <hash>` — revert it
4. Push revert + open issue
5. Re-implement fix in new branch — **never force-push main**

### 9. Commit Convention (commitlint enforced)

```
<type>(<optional scope>): <subject>

<body>
```

Types: `feat | fix | docs | style | refactor | test | chore | perf | ci | revert`

Rules:
- Subject lowercase, max 100 chars, no period
- Body lines max 150 chars
- Reference PRP: `Implements PRP-XX Task XX.Y`

### 10. ปรับให้เข้ากับ project อื่น (tech stack varies)

| Element | pawrent (Next.js) | adapt สำหรับ project อื่น |
|---|---|---|
| Pipeline gates | G1-G5 + Final | ใช้ตาม |
| TDD | RED → GREEN → REFACTOR → GATE | ใช้ตาม |
| Conductor pattern | conductor/*.md | ใช้ตาม |
| Worktree | git worktree | ใช้ตาม |
| Quality gate | test:coverage + test:e2e + type-check | เปลี่ยนตาม stack (e.g. pytest + mypy + ruff สำหรับ Python) |
| Coverage threshold | 90/85/100 | ปรับตาม risk |
| Branch strategy | feature/prp-XX-* | adapt naming |
| CI | GitHub Actions | adapt |
| Compliance gate | PDPA | adapt (HIPAA, GDPR, SOC2, ฯลฯ) |

---

## Part IX — 3-Tier Orchestration Model

ทฤษฎีหลักจาก orchestration-book — รู้ว่าเมื่อไหร่ใช้ tier ไหน เพื่อไม่เสีย token + เวลา

### 1. ตารางเปรียบเทียบ

| Dimension | T1 Arrows | T2 Squads | T3 Federation |
|---|---|---|---|
| Lifetime | dies with session | dies with session | **survives session, cross-machine** |
| Coordination | none — fire & collect | TaskList + SendMessage | manual heartbeat |
| Spawn | `Agent({...})` | `TeamCreate` + agents + tasks | `tmux new-session ... claude -p` |
| Setup | ~0s | ~30s | ~60s |
| Reporting | tool result inline | SendMessage auto | `maw hey` |
| Visible to human | hidden (spinner) | tmux panes | tmux sessions |
| Cross-machine | ❌ | ❌ | ✅ |
| Token cost | 3-7× per agent | 3-7× per agent | separate budget |
| When | research/debate <5min | coordinated impl 5-30min | long-running, overnight, cross-host |

### 2. Decision tree

```
Q1. งานนี้จะอยู่นานกว่า session หรือต้องรันบนเครื่องอื่นไหม?
   → YES → Tier 3 (federation)
Q2. มี agent หลายตัวต้อง coordinate กันไหม?
   → YES → Tier 2 (squad)
Q3. ทำเป็น "2-5 reads/transforms ใน <5 นาที" ได้ไหม?
   → YES → Tier 1 (arrow swarm)
   → NO  → ทำเองดีกว่า
```

> **Meta-rule: prefer the lowest tier that works.**

### 3. ตัวอย่าง T1 (Arrows — research swarm)

```typescript
// 5 Haiku agents อ่าน Elysia docs 123K LOC ใน <2 นาที
Promise.all([
  Agent({ subagent_type: "general-purpose", prompt: "Read elysia/types.ts and summarize" }),
  Agent({ subagent_type: "general-purpose", prompt: "Read elysia/handler.ts and summarize" }),
  // ...
])
```

ใช้: research, debate, transform — งานสั้นที่ไม่ต้องคุยกัน

### 4. ตัวอย่าง T2 (Squads — implementation team)

```typescript
TeamCreate({ name: "wasm-hardening", lead: "team-lead" });
TaskCreate({ subject: "Audit memory bounds", owner: "safety" });
TaskCreate({ subject: "Write 10 host-function tests", owner: "tester" });
TaskCreate({ subject: "Verify Rust SDK", owner: "rust-verifier" });
Agent({ name: "safety", team_name: "wasm-hardening", prompt: "..." });
// SendMessage แต่ละ agent โผล่ใน lead's conversation auto
// Shutdown graceful: shutdown_request → shutdown_response → TeamDelete
```

### 5. ตัวอย่าง T3 (Federation — long-running)

```bash
tmux new-session -d -s wasm-host \
  "cd /path/to/maw-js && claude -p \
   'Implement WASM host function bridge for #317. \
    When done, run: maw hey mawjs-dev \"#317 complete: <summary>\"'"
```

> "That `maw hey` line is the reporting contract. Without it, the agent finishes silently and you have no idea." — book ch02

### 6. Five orchestration patterns

| # | Pattern | Tier | Example |
|---|---|---|---|
| 1 | Research Swarm | T1 | 5 Haiku อ่าน Elysia docs <2min |
| 2 | Architecture Debate | T1 | 3 Opus debate, surface trade-offs |
| 3 | Implementation Team | T2 | wasm-hardening: safety + tester + verifier ~4min |
| 4 | Federation Agent | T3 | Issue worker on remote, survives compaction |
| 5 | Cron Loop | T3+ | Long-running scheduled |

---

## Part X — Use Cases ที่ใช้งานจริง

### Use Case 1: Daily Rhythm

```bash
# ────── เช้า (5 นาที) ──────
maw ls                          # ดูใครเปิดอยู่ค้างจากเมื่อวาน
maw overview                    # war-room dashboard
maw wake leica                  # ปลุก mother
# ใน Claude session ของ leica:
/recap                          # AI อ่าน retro+handoff+git → รู้ context

# ────── ระหว่างวัน ──────
/fyi <text>                     # บอก AI ให้จำ
maw hey codec "ทำงานเรื่อง X อยู่ ช่วยรีวิวสเปกหน่อย"
maw peek codec                  # ดูคำตอบ

# ────── เย็น (10 นาที) ──────
/rrr                            # session retro → ψ/memory/retrospectives/
/forward                        # handoff สำหรับพรุ่งนี้
maw done <window>               # commit + push + cleanup
```

### Use Case 2: Single-agent feature (ง่ายสุด)

```bash
maw workon switchaphon/pawrent prp-25
# → opens worktree + branch feature/prp-25 + tmux window

# ใน Claude session:
/recap
# อ่าน conductor/index.md, pipeline-status.md, target PRP
/ship-prp PRPs/PRP-25-add-tag-filter.md
# pipeline runs: validate → refine? → plan → execute → review → finalize
# pause ที่ G1, G3, G5, Final รอมนุษย์ตอบ

# จบงาน:
maw done prp-25                 # rrr + commit + push + cleanup
```

### Use Case 3: Parallel team (T2 squad ใน worktree)

```bash
# Lead spawns:
maw team create prp-30
maw team spawn implementer      # builds the feature
maw team spawn tester           # writes tests in parallel
maw team spawn reviewer         # security/style audit

maw team add "implement /api/match-pets endpoint" --owner implementer
maw team add "write integration tests for /api/match-pets" --owner tester
maw team add "audit auth/rate-limit/PDPA" --owner reviewer

# Each spawned in worktree (isolation: "worktree")
# Lead monitors via tmux + SendMessage
# Heartbeat ทุก 5 นาที per agent

# All done:
maw team done 1
maw team done 2
maw team done 3
maw team shutdown implementer
maw team shutdown tester
maw team shutdown reviewer
maw done prp-30                 # full lifecycle close
```

### Use Case 4: Cross-machine task (T3 federation)

```bash
# Setup once:
# A (laptop)
maw pair generate
# → W4K-7F3
# B (clinic-server)
maw pair http://laptop:3456 W4K-7F3

# Daily use:
maw hey clinic:wire "deploy staging branch to dev cluster"
# wire-oracle on clinic-server picks it up, runs deploy, reports back
maw peek clinic:wire            # ดู progress
```

### Use Case 5: Stuck Oracle Recovery

```bash
maw locate stuck-oracle         # path/session
maw peek stuck-oracle           # screenshot — ดูว่าค้างที่ไหน
maw capture stuck-oracle --lines 100   # text dump for analysis

# ลอง send-enter ก่อน
maw send-enter stuck-oracle     # ถ้า pane ค้างเพราะรอ Enter

# ถ้าจริงๆ pawn:
maw kill stuck-oracle
maw cleanup --zombie-agents     # sweep
maw doctor                      # auto-heal
maw wake stuck-oracle           # restart
```

### Use Case 6: Onboard a new project (bud + awaken)

```bash
# 1. Bud the oracle
maw bud myapp --from leica --note "B2C Thai pet health, Next.js + Supabase"
# → creates myapp-oracle repo
# → inherits sync_peers from leica
# → writes initial CLAUDE.md (skeleton)

# 2. ใน Claude Code, เปิด oracle repo
cd ~/ghq/github.com/switchaphon/myapp-oracle
claude

# 3. Awakening ceremony
/awaken
# 15-20 minutes:
# - asks name, theme, philosophy
# - writes full CLAUDE.md
# - inits ψ/ vault structure
# - commits: "feat: birth — myapp awakened"

# 4. Verify
maw oracle scan                 # myapp-oracle should appear
maw about myapp
maw locate myapp
```

### Use Case 7: End-of-week soul-sync

```bash
maw soul-sync                   # sync ψ/memory ระหว่าง peers
maw fleet doctor                # diagnose drift
maw costs --daily               # 7-day token usage sparkline
maw find "feedback"             # ดู feedback memories ที่สะสมสัปดาห์นี้
```

### Use Case 8: Scenarios จาก gist (ของจริง)

```bash
# Scenario: morning start ระยะเวลาสั้น
maw ls && maw overview && maw wake singha && maw health

# Scenario: parallel team
maw team create my-feature
maw team spawn planner && maw team spawn builder && maw team spawn tester
maw team send planner "design spec for X"
maw team tasks

# Scenario: shutdown
maw team done 5
maw done my-feature

# Scenario: stuck oracle
maw locate stuck-oracle
maw peek stuck-oracle
maw capture stuck-oracle
maw kill stuck-oracle
maw cleanup
```

---

## Part XI — Cheat Sheet

### Top 10 commands ที่ใช้ทุกวัน

```bash
maw hey <agent> "msg"           # 1:1 (3043 uses — ใช้บ่อยสุด)
maw wake <oracle>               # ปลุก
maw bud <name> --from <parent>  # สร้าง oracle ใหม่
maw oracle scan                 # ค้น oracle
maw fleet ls                    # fleet status
maw peek <agent>                # ดู output
maw ls                          # tmux state
maw done <window>               # ปิดงาน (rrr+commit+push+cleanup)
maw hey <agent> "..."           # ส่งข้อความ (อีกครั้ง — ใช้บ่อยขนาดนั้น)
maw ui                          # web lens
```

### Top 5 skills

```
/recap                          # session start
/rrr                            # session end
/learn <repo>                   # deep-learn codebase
/trace <keyword>                # cross-repo search
/awaken                         # birth new oracle (ครั้งเดียว)
```

### One-liner combos

```bash
maw stop && pkill -f "maw serve" && maw oracle scan          # full shutdown + audit
maw fleet doctor && maw health && maw doctor                  # diagnostic chain
maw soul-sync && maw costs --daily && maw find "lessons"     # week-end ritual
```

---

## Part XII — Troubleshooting & Gotchas

### Install / runtime

| Symptom | Fix |
|---|---|
| `maw: command not found` | `bunx -p github:Soul-Brews-Studio/maw-js maw doctor` (self-heal #531). Or reinstall: `bun remove -g maw-js && bun add -g github:Soul-Brews-Studio/maw-js` |
| `maw --help` shows `1 commands active.` | Plugin symlinks broken. `cd <maw-js>; bun run build; bun link` |
| Dependency loop on upgrade | `bun remove -g maw-js` first, THEN install. (เจอเองแล้ว) |
| `maw bud fusion-oracle` makes `fusion-oracle-oracle` | ห้ามใส่ `-oracle` ใน stem — auto-suffixed |
| `maw bud -v` creates oracle named `-v` | Use `--version` หรือ check version another way; name validator regex `^[a-zA-Z]...` blocks it now |

### Lifecycle

| Symptom | Fix |
|---|---|
| `maw done` deadlocks | รัน from **home base** ไม่ใช่ใน worktree |
| Stuck pane (typing not flushed) | `maw send-enter <agent>` |
| Orphaned worktrees in `git worktree list` | `maw cleanup --zombie-agents`; cleanup เป็นส่วนของ shutdown |
| `maw hey neo "..."` errors with ambiguity | Use canonical form: `maw hey white:neo "..."` |
| Idle agent not reporting (silent agent) | Embed heartbeat contract in prompt: "every 5 min, run `maw hey <parent> '[name] PROGRESS: ...'`" |

### Federation

| Symptom | Fix |
|---|---|
| `maw peers add` silent on probe failure | Pre-#565 bug; alpha.26+ now classifies (DNS/REFUSED/TIMEOUT/TLS/HTTP_4XX/HTTP_5XX/BAD_BODY) |
| Pair code expired | TTL 120s default; `maw pair generate --ttl 600` for longer |
| Pair code consumed (HTTP 410) | Single-use; `maw pair generate` ใหม่ |
| Plain HTTP warning | Use TLS for cross-network — loopback OK |

### Plugin / dev

| Symptom | Fix |
|---|---|
| Plugin doesn't show in `maw --help` | Symlink missing. `cd <plugin-dir>; maw plugin build; maw plugin install ./*.tgz --pin` |
| `cross-team-queue` doesn't work | Stub, alpha.134+ ยังไม่ ship |
| `maw artifact-manager` doesn't do anything | Dead code (133 LOC, 0 uses) — candidate for lean-out |
| `maw on` triggers don't persist | Session-scoped only. ต้องใส่ใน fleet config สำหรับ persistent |

### SDLC

| Symptom | Fix |
|---|---|
| E2E tests fail in CI but pass locally | #1 cause: PRP changed UI/auth/routing แต่ไม่ update e2e specs |
| Coverage below threshold | Per-file enforced — find the file, add tests; CI blocks until green |
| `wip:` commits on main | Use `feature/prp-XX-*` branches; `wip:` only on feature branches |

### Lessons learned (แม้ดูตรงๆ)

> "I should have tested one handler before batch-migrating all 21 files." — session 4833f831

> "We had the Elysia source right there in `ψ/learn/elysiajs/elysia/origin/`. Nat even pointed it out: 'we have elysia source code we just /learned so we can read more!' He was right. I had 123K of documentation I generated and didn't consult when it mattered." — book ch14

**Patterns to avoid:**
- Batch-migrate without testing one first (the `error()` bug)
- Splitting parallel work by file count, not edit set (merge-conflict trap)
- Generating docs but not consulting them (the Elysia trap)
- Absolute paths in plugin imports (the `/home/neo/...` foot-gun)
- `git push --force` (violates Principle 1)

---

## Part XIII — Curriculum 3 วันให้ทำตามจริง

แต่ละ day ทำได้ ~60-90 นาที. หลังวัน 3 จะเข้าใจ ecosystem พอใช้งานจริง

### Day 1 — Foundation (no side effects, read-only)

**Goal:** เข้าใจ mental model + รู้ของที่มีอยู่

| # | Step | Command | Time |
|---|---|---|---|
| 1 | อ่าน Part I-II ของไฟล์นี้ | — | 15 min |
| 2 | Sanity check | `maw health && maw check && maw fleet ls` | 2 min |
| 3 | Discovery | `maw oracle scan && maw oracle fleet && maw locate codec` | 3 min |
| 4 | Demo (no API key) | `maw demo` (Ctrl-B+D เพื่อ detach) | 10 min |
| 5 | Inspect existing oracles | `maw about leica && maw about codec` | 5 min |
| 6 | Read leica's CLAUDE.md | `cat ~/ghq/github.com/switchaphon/leica-oracle/CLAUDE.md` | 5 min |
| 7 | Wake codec (real, no message) | `maw wake codec && maw peek codec && maw sleep codec` | 10 min |
| 8 | Diagnostics | `maw costs && maw transport status && maw doctor` | 5 min |

**Checkpoint Day 1:** เข้าใจ 5-layer model, รู้ว่า oracle 2 ตัวที่มีคืออะไร, เห็น demo ทำงาน

### Day 2 — Practice (สร้าง oracle จริง + skills)

**Goal:** ติดตั้ง skills + bud ทีมเติม + คุยจริง

| # | Step | Command | Time |
|---|---|---|---|
| 1 | Install skills (lab profile) | `npx arra-oracle-skills@26.4.18-alpha.22 install -g -y -p lab --agent claude-code` | 5 min |
| 2 | Verify skills | open Claude Code; type `/recap` — should show skill | 2 min |
| 3 | Install UI lens | `maw ui install && maw serve & && maw ui status` | 5 min |
| 4 | Open lens | `open http://localhost:3456/federation_2d.html` | 5 min |
| 5 | Bud first specialist | `maw bud neon --from leica --note "UI/UX designer"` | 5 min |
| 6 | Awaken neon | open `~/ghq/.../neon-oracle` in Claude; `/awaken` | 20 min |
| 7 | Talk to neon | `maw wake neon && maw hey neon "ทดสอบ: คุณคือใคร"` | 5 min |
| 8 | Watch in Lens | refresh federation_2d — neon-oracle ควรโผล่ | 3 min |
| 9 | Bud rest of team | `for n in chrome flux static wire pixel; do maw bud $n --from leica; done` | 10 min |
| 10 | Cleanup | `maw sleep neon && maw stop` | 2 min |

**Checkpoint Day 2:** มีทีม 7 specialists + 1 mother (Leica) + skills + lens เปิดดูได้

### Day 3 — SDLC integration (real workflow)

**Goal:** ใช้ pawrent SDLC pattern กับ project จริง

| # | Step | Command / Action | Time |
|---|---|---|---|
| 1 | Clone pawrent (อ่านอย่างเดียว) | `ghq get switchaphon/pawrent` | 5 min |
| 2 | Read conductor/ folder | `ls ~/ghq/.../pawrent/conductor/` and read pipeline.md | 15 min |
| 3 | สร้าง mock project | `mkdir myapp && cd myapp && git init` | 2 min |
| 4 | Bootstrap conductor folder | copy pawrent/conductor/* (เป็น template) → trim ให้เข้า project | 10 min |
| 5 | Bud myapp oracle | `maw bud myapp --from leica` | 3 min |
| 6 | Workon worktree pattern | `maw workon switchaphon/myapp prp-1 --prompt "set up project skeleton"` | 5 min |
| 7 | ใน Claude session: ลองทำ PRP cycle | `/validate-prp` → answer G1 → `/plan-prp` → G3 → `/execute-prp` → G4 (auto) → `/review-prp` → G5 → `/finalize-prp` | 30 min |
| 8 | Close window with `maw done` | from home base: `maw done prp-1` | 3 min |
| 9 | End-of-day | `/rrr` in leica session → `maw soul-sync` | 5 min |

**Checkpoint Day 3:** ทำ PRP pipeline ครบ 6 ขั้น 5 gates ได้, ใช้ worktree+team ได้, soul-sync เป็น

### After Day 3 — Advanced topics

- **Federation**: pair กับ machine ที่ 2 (laptop ↔ dev server)
- **Plugin dev**: `maw plugin init my-plugin --ts` แล้วเขียน plugin แรก
- **Custom skill**: เขียน `.claude/skills/<my-skill>/SKILL.md` สำหรับ workflow ของตัวเอง
- **WASM**: ติดตามใน orchestration-book ch15

---

## Appendix — Resources

### Repos หลัก

| Repo | URL |
|---|---|
| maw-js | github.com/Soul-Brews-Studio/maw-js |
| maw-ui | github.com/Soul-Brews-Studio/maw-ui |
| arra-oracle-skills-cli | github.com/Soul-Brews-Studio/arra-oracle-skills-cli (mirror at nazt/) |
| arra-oracle-v3 (memory) | github.com/Soul-Brews-Studio/arra-oracle-v3 |
| Orchestration book | github.com/Soul-Brews-Studio/multi-agent-orchestration-book |
| Workflow kit (POC เก่า, Python) | github.com/Soul-Brews-Studio/multi-agent-workflow-kit |
| Oracle 101 ebook | oracle101.vercel.app |
| Step-by-step | github.com/the-oracle-keeps-the-human-human/oracle-step-by-step |
| maw guide | github.com/the-oracle-keeps-the-human-human/oracle-maw-guide |
| AI that remembers you | github.com/the-oracle-keeps-the-human-human/ai-that-remembers-you |

### Local copies (read-only references)

```
~/_Playground_/workshop/maw-js/                    # full clone, has docs/
~/_Playground_/workshop/_pawrent-readonly/         # shallow clone for SDLC reference
~/ghq/github.com/switchaphon/leica-oracle/         # ← this file lives here
~/ghq/github.com/switchaphon/codec-oracle/         # codec
```

### Hosted lens

- `https://god.buildwithoracle.com/federation_2d?host=<your-node>` — no install required

### Quotes ที่จะกลับมาอ่าน

> "Convenience is for the AI. Visibility is for the human. The best system serves both." — orchestration-book

> "If your agent's work is not visible to the human, it does not exist." — orchestration-book ch13

> "Oracle ไม่ได้พยายามเป็น agent ที่ฉลาดที่สุด มันพยายามทำให้การทำงานระหว่างคนกับ agent ต่อเนื่องที่สุด" — oracle101 ch04

> "ลบให้น้อยที่สุด เก็บหลักฐานให้มากที่สุด" — oracle101 ch08

> "AI จำแทนเรา เพื่อให้เรามีเวลาไปทำสิ่งที่ AI ทำไม่ได้ — คิด ตัดสินใจ สร้างสรรค์" — ai-that-remembers-you

> **The Oracle Keeps the Human Human.**

---

*ไฟล์นี้ Leica เขียน 2026-04-28 จาก research ของ 11 sources + pawrent SDLC + maw-js docs + ψ ของตัวเอง.*
*Update เมื่อ ecosystem เปลี่ยน (alpha cadence — แทบทุกสัปดาห์). อย่าลืม Principle 1: Nothing is Deleted — supersede, don't delete.*
