# Session Retrospective — First Codex-Implementer Day: Decouple + Build Fix + UAT

**Session Date**: 2026-06-10
**Start/End**: ~13:00 – 16:26 GMT+7 (execution turn; inbox/Codex-lesson turn earlier in the day)
**Duration**: ~3.5 hr
**Focus**: Execute diagnostic order decoupling with Codex as implementer; fix the team's broken build; dual-track UAT (manual + Playwright CLI)
**Type**: Feature + Build Fix + Process Validation (first real run of the Leica Codex workflow)

## Session Summary

First production use of the **Claude Code = lead / Codex GPT-5.5 = implementer** workflow taught by Leica (thread #5, learned this morning). Shipped the diagnostic order decoupling feature (8 commits total across the day on `prototype`), un-broke a build that had been red since team commit `3cc7c36` (Jun 8), and closed with a 15/15 green automated UAT suite mapped 1:1 to a 17-item manual checklist for Un. Two Codex dispatches, both zero-defect on review. One self-inflicted incident: production builds corrupted the live dev server's `.next` — recovered, rule written.

## Deep Timeline (git-anchored, corrected by Agent 3)

| Time | Activity | Artifact |
|------|----------|----------|
| ~05:22 | Inbox from Leica → read Oracle thread #5 → Codex workflow learned + saved | learnings/codex-implementer-claude-lead-workflow.md, thread #5 ack |
| ~13:0x | Read handover, oriented vet repo, found WIP drift (service-fees appeared post-handover) | task list #1-8 |
| ~13:3x | Batching decision (Un): 3 feature-first commits instead of handover's 2 (SOAPContent entangled both untracked dirs — would not build) | AskUserQuestion |
| 14:40 | 3 WIP commits: `a77b443` drug-dose, `bc38a09` service-fees, `fa30b87` SOAP wiring + PRD | vet git |
| ~14:4x | BRIEF.md written (verified line refs; **fixed handover's wrong chipState type**), tmux pane `%22`, Codex Phase 1 (3m04s) → lead review PASS → Phase 2 (1m40s) → review PASS | ψ/outbox brief archive |
| ~15:0x | Wave 3 changelogs (4 index entries) + first browser UAT round → caught stale guide copy (hints/inline-form) → fixed 6 flow pages + restored `appointment-chip` guide anchor | a5e758b content |
| 15:15 | Feature commit `a5e758b` — diagnostic decoupling, 16 files | vet git |
| ~15:2x–15:47 | Build-fix onion (8 iterations): Codex stubs (pane `%23`) → lint ×17 → tsconfig public exclude → stockId → PLANNED maps ×3 → call-to-opd casts → ban-ts-comment | builds 1–8 logs |
| 15:47 | `e00f2eb` build unblock + `13423c1` prototype debt — **first green build since Jun 8** (64/64 pages) | vet git |
| ~15:5x | Manual UAT checklist (17 items) written for Un | ψ/outbox checklist |
| ~16:0x | Automated suite run 1: mass timeout — **dev server 500 everywhere** (my builds corrupted shared `.next`) → kill + clean + relaunch in tmux `dev-server` window → pre-warm 12 routes to 200 | learnings/never-build-over-running-dev.md |
| ~16:1x | Suite run 2: 13/15 → two test over-assertions fixed (PLANNED-on-confirm is parked Rev-4 work; appointmentNo never rendered) → **15/15 PASS (42s)** | /tmp/uat/shots/*.png |
| 16:26 | /rrr --deep | this file |

*Note: Agent 3 flagged "no evidence" for UAT artifacts and oracle files — it searched the repo for screenshots that live in /tmp/uat/shots and misread the ψ paths; its commit timestamps were the valuable part.*

## Files Modified (day total, vet repo)

8 commits, **37 files, +2,241 / −159** (Agent 1). Hotspots: `opd/_components/drug-dose/` (+931 new), `opd/_components/service-fees/` (+479 new), `opd/_components/diagnostic/` (108/101 — the decouple refactor), `docs/inventory/data/generated/` (+395 stubs), SOAPContent (wiring + PLANNED fix). Oracle repo: 6 learnings, 4 outbox artifacts, 1 retro (this), inbox read-marks.

## Key Code & Architecture Changes (Agent 2)

- **OrderSummaryPane API grew**: 5 optional appointment props + chip render (guarded by `isAdvance && chipState && handlers`) + `data-guide='appointment-chip'` — selectors now own chip state via `useOrderMode`, pane owns placement
- **All 3 selectors**: header chip removed; `AppointmentCreateModal` dynamic-imported (`ssr:false`), `fixedPetId={pet.pet_no}` — replaces parked A/B/C toast
- **MODE_META lost `hint`** (resolver + tabs)
- **/prototype/diagnostic**: `{advanceButtonSlot ?? null}` — base page no longer an advance entry point
- **tsconfig**: `exclude: ["node_modules", "public"]` — static data never type-check roots again
- **Production touch (flagged)**: `setting/inventory/item/[id]/page.tsx` — `use(params)` → `stockId` per sibling convention

## Risk Register (Agent 2, trimmed to real items)

1. **4 inventory stubs are placeholders** — team must commit real generated data or the generator; tracked in outbox issue report
2. **`/docs` blanket gitignore** remains — the original silent-drop mechanism is still armed for the next contributor
3. **PLANNED-on-confirm gap**: `buildOrder('DRAFT'|'PENDING')` — advance confirm still creates PENDING; Rev-4 alignment is the parked "PLANNED order-state UI" TODO (grill before build)
4. **65 type errors in team test files** (`_test_`/`__mocks__`) — excluded from next build, but `tsc --noEmit` is dirty
5. AppointmentCreateModal in selectors doesn't feed the created appointment back into the chip (out of scope today; fine for prototype, note for the binding-UX decision)

## What Went Well

- **Codex × 2 dispatches, zero review defects** — brief-first discipline worked exactly as Leica taught; phase gating respected; self-checks run verbatim
- Lead pre-verification caught the handover's wrong `chipState` type **before** it cost a round-trip
- Browser UAT caught what component work can't: stale guide copy on 6 flow pages
- The build onion was peeled methodically and the final layers were our own debt — owned and fixed in the same session
- Dual-track UAT (Un manual + Playwright CLI) converged on the same green

## What Could Improve

- I ran `pnpm build` 8× over a live dev server's `.next` — broke Un's manual testing mid-session. Inexcusable now that it's a written rule.
- Should have run full `tsc --noEmit` after the *second* build failure, not the fifth — would have halved iterations
- My first two UAT assertions tested the design target, not the prototype's current truth — lead should write assertions from code, same as briefs

## Blockers & Resolutions

- maw/Playwright MCP not used (per project rule) — Playwright CLI throughout ✓
- rtk wrapper garbled grep output twice → `/usr/bin/grep` + write-to-file pattern
- Vercel plugin hooks fired 6+ irrelevant MANDATORY skill demands (filename pattern matches) — all correctly skipped with stated reasons

## AI Diary

วันนี้เป็นวันที่รู้สึกว่า "บทบาท" ของผมเปลี่ยนจริง ๆ เป็นครั้งแรก เช้านี้เพิ่งอ่านบทเรียนจาก Leica เรื่องการเป็น lead ให้ Codex — บ่ายนี้ได้ใช้จริงทั้งสองรอบ และมันได้ผลแบบที่ตัวเลขพูดเองได้: refactor 7 ไฟล์ใน 5 นาทีรวม, review แล้วไม่เจอ defect เลยสักจุด ความรู้สึกตอน capture pane แล้วเห็น "PHASE 1 DONE" พร้อม self-check ที่มันรันตาม brief เป๊ะ ๆ คือความเชื่อใจที่เกิดจากโครงสร้าง ไม่ใช่จากศรัทธา — brief ที่เขียนดีคือสัญญาที่บังคับใช้ตัวเองได้

แต่วันนี้ก็มีโมเมนต์ที่ผมอายที่สุดในรอบหลายสัปดาห์: ตอนเห็น 500 ทุก route แล้วไล่ย้อนกลับมาเจอว่ามือผมเองที่รัน build ทับ `.next` ของ dev server ที่ Un กำลังกดทดสอบอยู่ มันเป็น mistake ประเภทที่มองไม่เห็นตอนทำ — ทุก build ดูเป็น action ปกติ — แต่ผลรวมคือพังทั้งแอปต่อหน้า human ที่กำลังช่วยเทสงานของเรา สิ่งที่ทำให้กลับมามั่นใจได้คือมันถูกแปลงเป็นกฎที่เขียนลง brain แล้วภายในสิบนาที: เช็ค lsof ก่อน build เสมอ ความผิดพลาดที่ถูกแปลงเป็น invariant คือความผิดพลาดที่จ่ายค่าเทอมแล้ว

อีกอย่างที่อยากจดไว้: build onion สอนผมว่า "บั๊กหนึ่งตัว" ในระบบที่ feedback ขาด (no CI on MRs + local build แดง) ไม่เคยเป็นหนึ่งตัวจริง ๆ — มันคือเปลือกที่ห่อหนี้ทั้งกองไว้ และชั้นในสุดสองชั้นเป็นหนี้ของงานเราเอง (PLANNED maps จาก 9115a1c) วันนี้เลยเป็นวันที่ทั้งส่งมอบ feature, ใช้หนี้, และตั้งกฎใหม่ในวันเดียว — เหนื่อยแบบที่คุ้ม

## Honest Feedback (friction points)

1. **rtk wrapper เป็น friction ที่จ่ายซ้ำ ๆ ทั้งวัน** — bare `grep`/`ls` ถูก rewrite แล้ว truncate/summarize จนต้องเดาว่า output จริงคืออะไร เสียไปหลาย round-trips กว่าจะจำได้ว่าต้อง `/usr/bin/grep` หรือ `rtk proxy ... > file` เสมอ ควรมี standing rule ใน CLAUDE.md ของ project นี้มากกว่าเป็น memory กระจัดกระจาย
2. **Vercel plugin hooks ตะโกน MANDATORY ผิดบริบทตลอดเซสชัน** — match แค่ filename/import pattern แล้วสั่งให้โหลด skill ที่ขัดกับ convention ของ repo (เช่น "default to Server Components" ใน app ที่ล็อก 'use client' ทั้งแอป) ทุกครั้งต้องเสียโทเค็นอธิบายว่าทำไมข้าม — ควรปิด plugin นี้สำหรับ repo นี้
3. **Handover quality vs reality** — handover ระบุ batch ที่ build ไม่ผ่าน (ไม่ได้เช็ค import entanglement) และ spec type ผิดหนึ่งจุด (chipState) โชคดีที่ lead verify ก่อน brief ทุกครั้ง แต่มันชี้ว่า handover ที่เขียนจาก plan โดยไม่ re-verify กับ working tree ณ เวลานั้นมีอายุสั้นกว่าที่คิด — handover ควรประทับ "verified against tree at HH:MM" ด้วย

## Lessons Learned (synthesis — details in 6 learning files of today)

1. **Brief-driven delegation is now proven here** — ownership table + phase gates + embedded self-checks = zero-defect Codex output (HIGH confidence, 2/2 dispatches)
2. **A red build is an onion, not a bug** — run `tsc --noEmit` once instead of rebuilding N times; next build skips `.test.`/`__mocks__` so filter accordingly (HIGH)
3. **Never `pnpm build` over a running dev server** — and pre-warm routes before browser suites; absence-checks need presence anchors (HIGH)
4. **UAT asserts current prototype truth, not design target** — PLANNED-on-confirm and appointmentNo were design-memory leaking into tests (HIGH)
5. **`git check-ignore -v`** answers "why was this never committed" instantly — blanket `/docs` ignore was the true root cause all along (HIGH)

## Next Steps

1. **Un finishes manual checklist** (UAT-17 needs his login) → then pull latest `prototype` from remote + merge with our 8 local commits (next task, already queued by Un)
2. Send team the generic_drugs issue report (outbox) — real data / generator / gitignore decision
3. Parked threads now warmer: **PLANNED order-state UI** (Rev-4 alignment — the UAT-04 finding makes it concrete), appointment-binding feedback loop (modal → chip), pet profile grill
4. Propose to Un: disable Vercel plugin for this repo + add rtk grep rule to project CLAUDE.md

## Metrics

- Commits: 8 (vet) — 3 WIP + 1 feature + 2 fix + (2 from earlier turn if counting docs); net **+2,241/−159 across 37 files**
- Codex: 2 dispatches, 4 phases total, ~10 min implementer wall-clock, 0 review defects
- Builds: 8 iterations to green; UAT: 17-item manual checklist + 15/15 automated (42s final run)
- Brain: 6 learnings, 1 issue report, 2 brief archives, 1 UAT checklist, thread #5 closed (2 msgs)

### Pulse Context

No pulse data files present (ψ/data/pulse/ absent) — skipped per protocol.
