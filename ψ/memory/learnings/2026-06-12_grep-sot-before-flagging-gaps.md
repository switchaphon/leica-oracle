# Grep SOT docs ก่อนประกาศ gap + NULL เป็น discriminator ฟรีใน PG

**Date**: 2026-06-12
**Source**: pops/app/vet — grill session Diagnostic Slot Ownership (Q1–Q14)

## Lesson 1 — SOT flow docs ตอบไว้แล้วเกือบทุกอย่าง

ผม flag "diagnostic order ไม่มีทางผูก appointment ใน DB จริง" เป็น known gap ทั้งที่ `prototype/docs/diagnostic-flow.html` §4 Rev 4 ออกแบบ `appointment_id` FK + partial CHECK constraint ไว้ครบแล้ว — user ต้องชี้กลับไปที่ doc

**Rule**: ในโปรเจกต์ pops/vet ก่อนพูดว่า "ระบบยังไม่มี X" ต้อง grep `src/app/prototype/docs/*.html` ก่อนเสมอ — flow docs ละเอียดถึงระดับ SQL constraint และ revision history (Rev tags + grill dates ใน header)

## Lesson 2 — PostgreSQL NULL ≠ NULL = zero-migration discriminator

`UNIQUE (vet_id, appointment_time)` ไม่ block แถวที่ vet_id IS NULL หลายแถว (default NULLS DISTINCT) → "นัดไม่ผูกหมอ ไม่ล็อค slot" ได้ด้วย `ALTER COLUMN vet_id DROP NOT NULL` บรรทัดเดียว ไม่แตะ index ไม่เพิ่ม column

ระวัง: ห้ามใช้ `NULLS NOT DISTINCT` (PG15+) กับ index นั้น และทุก query ที่ INNER JOIN ผ่าน column นั้นจะกลืนแถว NULL หายเงียบ ๆ — ต้อง audit เป็น LEFT JOIN

## Lesson 3 — Slot-based vs queue-based ต้องถามหน้างาน

ผม assume ห้องทุกห้องจอง slot แบบห้องตรวจหมอ — จริง ๆ ห้อง lab เป็นคิว (ใครมาก่อนทำก่อน เวลาทับกันได้) ทำให้ unique constraint บนห้องผิดความเป็นจริง การ model resource scheduling ต้องถามก่อนว่า resource นั้น exclusive ต่อช่วงเวลาไหม
