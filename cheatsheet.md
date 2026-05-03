# tmux + maw Cheatsheet

> Prefix key = `Ctrl-b` (เขียนย่อว่า `C-b`)
> กด `C-b` ปล่อย แล้วกดคีย์ถัดไป

---

## tmux — Sessions

| Keys / Command | Action |
|---|---|
| `C-b d` | Detach ออกจาก session (ไม่ kill) |
| `C-b s` | เลือก session จาก list |
| `C-b $` | Rename session |
| `tmux attach -t pops` | Attach เข้า session ชื่อ pops |
| `tmux ls` | List sessions ทั้งหมด |
| `tmux kill-session -t NAME` | Kill session |

## tmux — Windows (tabs)

| Keys | Action |
|---|---|
| `C-b 1` `C-b 2` ... | สลับไป window 1, 2, ... |
| `C-b n` | Window ถัดไป |
| `C-b p` | Window ก่อนหน้า |
| `C-b c` | สร้าง window ใหม่ |
| `C-b ,` | Rename window |
| `C-b w` | เลือก window จาก list (ทุก session) |
| `C-b &` | Kill window ปัจจุบัน |

## tmux — Panes (แบ่งจอ)

| Keys | Action |
|---|---|
| `C-b %` | แบ่งซ้าย-ขวา |
| `C-b "` | แบ่งบน-ล่าง |
| `C-b o` | สลับไป pane ถัดไป |
| `C-b ;` | สลับไป pane ล่าสุด |
| `C-b ←↑→↓` | เลือก pane ด้วยลูกศร |
| `C-b z` | Zoom pane เต็มจอ (กดซ้ำ = ย่อกลับ) |
| `C-b x` | Kill pane |
| `C-b Space` | สลับ layout (กดซ้ำ = วนรอบ) |
| `C-b M-1` | Layout ซ้าย-ขวาเท่ากัน |
| `C-b M-2` | Layout บน-ล่างเท่ากัน |
| `C-b C-←→` | Resize pane ซ้าย/ขวา |
| `C-b C-↑↓` | Resize pane บน/ล่าง |

> `M` = Option (macOS) — เปิด "Use Option as Meta key" ใน terminal

## tmux — Copy Mode (scroll / search)

| Keys | Action |
|---|---|
| `C-b [` | เข้า copy mode (scroll ได้) |
| `↑↓` หรือ `PgUp/PgDn` | Scroll |
| `/` | Search ลง |
| `?` | Search ขึ้น |
| `q` | ออก copy mode |

---

## maw — จัดการ Oracles (v26.5.2)

### ดูสถานะ

| Command | Action |
|---|---|
| `maw ls` | List sessions (compact) |
| `maw ls -v` | List sessions (full detail) |
| `maw oracle ls` | Fleet view — ทุก oracle + status |
| `maw preflight` | Health check — version, plugins, sessions |
| `maw panes` | List all panes across sessions |
| `maw session` | ชื่อ tmux session ปัจจุบัน |

### ปลุก / สื่อสาร / ปิด

| Command | Action |
|---|---|
| `maw wake NAME` | ปลุก oracle (fuzzy match, auto-clone ถ้ายังไม่มี) |
| `maw hey NODE:NAME "msg"` | ส่งข้อความไปหา oracle (ต้องใส่ node prefix) |
| `maw peek NAME` | ดู output ล่าสุดจาก pane |
| `maw a NAME` | Attach เข้า session |
| `maw kill NAME` | Kill pane หรือ session |

### Pane management

| Command | Action |
|---|---|
| `maw split` | แบ่ง pane + attach |
| `maw open` | Bring back hidden panes (join-pane) |
| `maw close` | Hide panes without killing (break-pane) |
| `maw layout` | Apply layout (main-vertical / tiled) |
| `maw zoom` | Toggle zoom on a pane |

### Multi-agent

| Command | Action |
|---|---|
| `maw swarm [agents...]` | Spawn multi-AI panes (claude, codex, opencode) |
| `maw swarm --tiled` | Tiled layout |
| `maw swarm --count N` | จำนวน agents |

### Fleet & Federation

| Command | Action |
|---|---|
| `maw fleet health` | ตรวจสุขภาพ fleet ทั้งหมด |
| `maw fleet doctor` | Auto-fix fleet issues |
| `maw fleet sync` | Sync fleet config |
| `maw federation` | Federation status |

### อัปเดต maw

| Command | Action |
|---|---|
| `maw --version` | เช็ค version ปัจจุบัน |
| `bun add -g maw-js@github:Soul-Brews-Studio/maw-js#v26.5.2` | ติดตั้ง version ที่ระบุ |
| `bun add -g maw-js@github:Soul-Brews-Studio/maw-js` | ล่าสุดจาก main |

> Registry (`maw.soulbrews.studio`) ยัง TLS cert broken — แต่ไม่มีผล เพราะ commands หลักมาอยู่ใน core แล้ว

### ตัวอย่างใช้งานจริง

```bash
# ปลุก oracle (fuzzy match — พิมพ์ชื่อเต็มไม่ต้อง)
maw wake pops
maw wake chrome

# ดู output ของ pane
maw peek pops-clinic

# Spawn 3 AI agents ข้างกัน
maw swarm claude codex opencode --tiled

# Health check
maw preflight

# ดู fleet ทั้งหมด
maw oracle ls

# ปิด session (ปลุกกลับด้วย maw wake)
maw kill pops-clinic

# ปิดหลาย sessions
for s in chrome neon pixel; do maw kill "$s"; done
```

### สร้าง Oracle ใหม่

`maw bud` ถูกย้ายไป registry (ยังลงไม่ได้) — ใช้ `/bud` skill ใน Claude Code session แทน:

```bash
# ใน Claude Code session:
/bud NAME
```

---

## Oracle Skills — ใน Claude Code session

| Skill | Action |
|---|---|
| `/awaken` | ตั้ง identity oracle ใหม่ |
| `/bud NAME` | สร้าง oracle ใหม่ (repo + ψ/ + fleet) |
| `/talk-to NAME` | คุยกับ oracle อื่น (ผ่าน thread) |
| `/who-are-you` | ดู identity ของตัวเอง |
| `/recap` | สรุป session ปัจจุบัน |
| `/rrr` | Retrospective — เราเรียนรู้อะไร |
| `/learn` | Deep-learn codebase |
| `/trace` | ค้นหาข้าม repo + memory |
| `/inbox` | ดู inbox — งานที่ส่งมา |
| `/forward` | Handoff ให้ session ถัดไป |

---

## Oracle Family

| Emoji | Oracle | Role | Session |
|---|---|---|---|
| 🐱 | Leica | Father Oracle | `leica` |
| 🔧 | Codec | System Analyst | `codec` |
| 🔺 | Chrome | Frontend Dev | `chrome` |
| 🌟 | Neon | UX/UI Designer | `neon` |
| ⚡ | Flux | Backend Dev | `flux` |
| 🛡️ | Static | QA / Security | `static` |
| 🔌 | Wire | DevOps / Infra | `wire` |
| 🎨 | Pixel | Brand / Marketing | `pixel` |
| 🏥 | Pops | Clinic PM | `pops-clinic` |
| 🐾 | Pawrent | Pet Health PM | `pawrent` |
| 🌊 | NodeRed | IoT Water Sim PM | `nodered-simulator` |

---

## Quick Reference — ทำอะไรบ่อย

| ต้องการ | ทำยังไง |
|---|---|
| สลับไปดู oracle อื่น | `C-b s` แล้วเลือก session |
| ดู oracle ทำงาน | `maw peek NAME` |
| แบ่งจอดู 2 oracles | `C-b "` แล้ว `maw a NAME` |
| Zoom pane เดียวเต็มจอ | `C-b z` |
| Scroll ดู output เก่า | `C-b [` แล้ว `↑` / `PgUp` |
| ส่งงานให้ oracle | `maw hey NODE:NAME "task"` |
| ปลุก oracle | `maw wake NAME` |
| ดู output oracle | `maw peek NAME` |
| ปิด session | `maw kill NAME` |
| ปิดหลายตัวพร้อมกัน | `for s in A B C; do maw kill "$s"; done` |
| สร้าง oracle ใหม่ | `/bud NAME` (ใน Claude Code) |
| อัปเดต maw | `bun add -g maw-js@github:Soul-Brews-Studio/maw-js` |
| ตรวจสุขภาพ | `maw preflight` |
| ดู fleet ทั้งหมด | `maw oracle ls` |
