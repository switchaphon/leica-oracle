# Codex Trap #11 — workspace-write บล็อก .git/index.lock

**Date**: 2026-06-13
**Source**: leica inbox — ratchada เจอจริงระหว่างทำ PRD #2 condo-parking-bot

## Lesson

`codex exec -s workspace-write` commit ไม่ได้ — `fatal: Unable to create .git/index.lock: Operation not permitted`

sandbox อนุญาตเขียนไฟล์ใน workdir แต่บล็อก `.git/` directory → git commit, git add ทำไม่ได้

## วิธีเลี่ยง

1. **Oracle lead commit** (recommended) — ให้ Claude Code (full access) commit แทน สอดคล้องกับ review flow อยู่แล้ว
2. **`-s danger-full-access`** — ปลดล็อคทุกอย่าง แต่เสี่ยงกว่า

## ความสัมพันธ์กับ Trap อื่น

- **Trap #2**: workspace-write เขียนนอก workdir ไม่ได้ (เช่น ~ หรือ /tmp)
- **Trap #11**: workspace-write เขียนใน `.git/` ไม่ได้ แม้อยู่ใน workdir

ทั้งสอง trap เป็น sandbox boundary — Trap #2 กว้าง (path), Trap #11 แคบแต่ critical (git internals)
