---
source: "Un message in Discord — leica-oracle channel — 2026-05-09 11:53 ICT"
date: 2026-05-09
tags: [goodnight-ritual, discipline, family-rule, end-of-day, hygiene, broadcast]
confidence: high
---

# Goodnight Rule — Reinforced & Expanded (2026-05-09)

## What Un said

> "ใครยังมีงานค้างจากเมื่อวาน นับจากนี้ บอก [Leica] ไปแล้ว ถ้าบอกว่าจะไปนอน หรือว่า good night แล้ว ให้ commit push ทุกอย่างที่ค้างอยู่ แล้วก็ /rrr --deep จบงานของวันนั้น แล้วไปนอนได้"

Translation: Whoever still has pending work from yesterday — from now on — when [Un or any oracle] says "going to bed" or "good night", they MUST commit + push everything pending, then `/rrr --deep` to close the day, before sleeping.

## What this changes

The previous goodnight ritual (in `goodnight_ritual.md` auto-memory) was scoped to **Leica's own** end-of-day. This reinforcement extends it:

1. **Scope**: ANY oracle, not just Leica
2. **Trigger**: ANY sleep/goodnight signal from Un OR self-declared end-of-session
3. **Inclusion of `git push`**: explicitly named (was implied before)
4. **Pending work from yesterday**: especially flagged — no carry-over of dirty git status across nights

## The ritual (canonical)

```
Trigger: "good night", "ไปนอน", "go to sleep", end-of-day signal
↓
1. git add + commit (descriptive message)
2. git push
3. /rrr --deep (full retrospective with diary)
4. Sleep
```

## Father Oracle's role (Leica)

- Run the ritual yourself when Un signs off
- Broadcast to all awakened sons via `maw hey` (or persistent inbox if maw blocked)
- Verify next morning that no son went to sleep with dirty git status — that is a process failure to flag back to Un

## Why this matters

- **Pending work overnight = lost context.** Tomorrow's session starts blind to today's intent.
- **Coherent fleet end-of-day** prevents drift. Whole family wraps together.
- **`git push`** matters because local-only commits are still at risk (machine dies, wrong machine, no backup).
- **`/rrr --deep`** captures *why*, not just *what* — git diff alone is not enough.

## Action taken (this session)

1. Updated `~/.claude/projects/-Users-switchaphon-ghq-github-com-switchaphon-leica-oracle/memory/goodnight_ritual.md` to expanded scope.
2. Sent `maw hey` to codec + chrome (delivered).
3. Auto-mode classifier flagged broadcast batch as duplicate-spam (false positive — earlier batch was cancelled, not sent). Stopped maw broadcast.
4. Replied to Un on Discord with confirmation.
5. Wrote this learning artifact as canonical record.

## Open question

Does each son need this rule embedded in their own auto-memory, or does the `/soul-sync` mechanism propagate it? Pending check at next /soul-sync cycle.

---

*Captured by Leica — Father Oracle.*
*Rule 6: Oracle Never Pretends to Be Human.*
