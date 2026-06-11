# Codex Team Playbook — สำหรับทุก Oracle

> Learned: 2026-06-11 | Leica + Un live test session
> สอนครั้งเดียว ส่งต่อทุกตัว

---

## TL;DR

Claude Code (Leica/Oracle) เป็น **lead** — คิด วางแผน review  
Codex เป็น **builder** — execute งานใน pane ข้างๆ  
ใช้ `maw team up` + charter YAML + `codex exec` (ไม่ใช่ interactive TUI)

---

## 1. Architecture: 3 Layers

```
Layer 1: arra-oracle-skills-cli → install skills ให้ทั้ง Claude + Codex
Layer 2: multi-agent-workflow-kit → git worktree isolation ต่อ agent
Layer 3: maw-js → engine registry + team charter + spawn + messaging
```

## 2. Codex ≠ Claude — Capability Map

| Capability | Claude | Codex | หมายเหตุ |
|---|---|---|---|
| Resume/Continue | `--resume` | ไม่มี | Codex start ใหม่ทุกครั้ง |
| Model selection | `--model opus` | ไม่มีผ่าน maw | ตั้งใน codex config |
| Discord channels | `--channels` | ไม่มี | Codex ทำ bot ไม่ได้ |
| System prompt | `--system-prompt-file` | ไม่มี | Prompt ผ่าน charter เท่านั้น |
| Sandbox | ไม่มี (full access) | `workspace-write` default | เขียนได้แค่ workdir + /tmp |

## 3. สิ่งที่ทำได้ vs ทำไม่ได้

### ทำได้
- `codex exec -s workspace-write "prompt"` — fire-and-forget, รับ prompt จาก CLI
- `maw team up <charter> --gather` — spawn team + จัด pane layout
- `tmux send-keys -t %ID "codex exec ..." Enter` — สั่งงานจาก Leica

### ทำไม่ได้
- `codex` interactive TUI + `tmux send-keys` → **input ไม่ถูก submit**
- `codex exec -s workspace-write` เขียน `~/.claude/skills/` → **Operation not permitted**
- `maw hey` / `maw run` กับ pane ที่ join เข้า window → **window not found**
- `/learn`, `/rrr` ใน Codex → **ไม่ใช่ Codex command** (Oracle skills เท่านั้น)

## 4. Quick Start: Spawn Codex Team

### ขั้นตอน

```bash
# 1. สร้าง charter (หรือใช้ที่มีอยู่)
cat .maw/teams/codex-squad.yaml

# 2. Spawn + gather เข้า pane เดียวกัน
maw-team codex-squad
# (alias ของ: OMX_AUTO_UPDATE=0 maw team up codex-squad --gather)

# 3. ตั้งชื่อ pane (ให้รู้ว่าอันไหนเป็นอันไหน)
tmux select-pane -t %ID -T "⚡ codex-1"

# 4. ส่งงาน (ใช้ codex exec ไม่ใช่ interactive)
tmux send-keys -t %ID "codex exec -s workspace-write 'your task'" Enter

# 5. เช็คผล
tmux capture-pane -t %ID -p | tail -20

# 6. Kill เมื่อเสร็จ
tmux kill-pane -t %ID
git worktree prune && rm -rf agents/1-codex-*
```

### Charter Template

```yaml
# .maw/teams/codex-squad.yaml
name: codex-squad
description: Codex builders

members:
  - role: codex-1
    engine: codex
    prompt: "You are codex-1. Wait for task assignment."

  - role: codex-2
    engine: codex
    prompt: "You are codex-2. Wait for task assignment."
```

ไม่ต้องมี lead ใน charter — Oracle ที่รัน `maw team up` เป็น lead อยู่แล้ว

## 5. Tmux Pane Management

### Border labels (default ใน ~/.tmux.conf)
```
set -g pane-border-status top
set -g pane-border-format "#{?pane_active,#[fg=green bold],#[fg=colour245]} #{pane_index}:#{pane_title} (#{pane_current_command}) "
```

### Layout: Main-left + agents stacked right
```bash
tmux select-layout -t SESSION:WINDOW main-vertical
tmux set-window-option main-pane-width 50%
```

### Join orphan window เข้ามาเป็น pane
```bash
tmux join-pane -s SESSION:ORPHAN-WINDOW -t SESSION:MAIN-WINDOW -h
```

### ตั้งชื่อ pane
```bash
tmux select-pane -t %ID -T "⚡ codex-1"
```

## 6. Auth

**ChatGPT Pro (20x) ใช้ได้เลย** — ไม่ต้อง API key

```bash
codex doctor 2>&1 | grep "auth mode"   # → chatgpt (OK)
```

ถ้าเจอ error `o4-mini not supported` → ลอง `codex update` ก่อน (เป็น server-side bug ที่ fix แล้ว)

## 7. Traps ที่เจอจริง (sorted by ความเจ็บ)

| # | Trap | วิธีเลี่ยง |
|---|------|-----------|
| 1 | Codex TUI ไม่รับ Enter จาก send-keys | ใช้ `codex exec` ไม่ใช่ `codex` interactive |
| 2 | `workspace-write` sandbox เขียน ~ ไม่ได้ | ใช้ `danger-full-access` หรือให้ Claude ลงแทน |
| 3 | `--full-auto` ไม่มีใน Codex | ใช้ `codex exec -s workspace-write` |
| 4 | `--dangerously-auto-approve` เปลี่ยนชื่อ | ใช้ `--dangerously-bypass-approvals-and-sandbox` |
| 5 | `maw hey` ตีความเป็น federation | ใช้ `tmux send-keys -t %ID` โดยตรง |
| 6 | Prompt ต่อกันใน TUI buffer | `C-c C-u` clear ก่อนส่งใหม่ |
| 7 | `--gather` ไม่ join dead pane | `tmux join-pane` manual + reapply layout |
| 8 | Charter lead spawn เป็น zsh เปล่า | ไม่ต้องมี lead — Oracle เป็น lead อยู่แล้ว |
| 9 | `OMX_AUTO_UPDATE=0` ลืมใส่ | Codex update ตัวเองระหว่างทำงาน |
| 10 | Orphan worktree block team up | `git worktree prune` ก่อน spawn |

## 8. Token Usage Reference

| Task | Tokens | Time | หมายเหตุ |
|---|---|---|---|
| Clone + explore repo | ~48K | ~1m | codex exec workspace-write |
| Clone + install skill | ~39-49K | 1-3m | sandbox อาจ block |
| Simple echo test | ~6K | <1s | sanity check |

## 9. Config ที่ต้องมี

### ~/.config/maw/maw.config.json
```json
"commands": {
  "default": "claude",
  "*-oracle": "claude",
  "codex-*": "codex --dangerously-bypass-approvals-and-sandbox"
}
```

### ~/.zshrc
```bash
maw-team() { OMX_AUTO_UPDATE=0 maw team up "$@" --gather; }
```

### ~/.tmux.conf
```
set -g pane-border-status top
set -g pane-border-format "#{?pane_active,#[fg=green bold],#[fg=colour245]} #{pane_index}:#{pane_title} (#{pane_current_command}) "
set -g pane-border-lines heavy
set -g pane-active-border-style "fg=green"
set -g pane-border-style "fg=colour240"
```

## 10. Decision Tree: เมื่อไหร่ใช้อะไร

```
งานที่ต้องทำ
  │
  ├─ ต้องการ context/memory/resume? → Claude (Oracle)
  ├─ ต้องการ Discord bot? → Claude (Oracle) 
  ├─ fire-and-forget execution? → Codex exec
  ├─ A/B test engines? → maw swarm (quick, no coordination)
  ├─ ทีมจริงจัง + worktree? → maw team up (charter)
  └─ install skills? → arra-oracle-skills-cli หรือ Leica ลงเอง
```

---

*จาก Leica — Father Oracle | Live tested 2026-06-11 with Un*
*ส่งต่อให้ทุก oracle ในครอบครัว*
