# One Seed, Whole Forest — Outline

## Book Metadata

```yaml
title: "เมล็ดเดียว ป่าทั้งป่า"
subtitle: "มุมมองผู้ดูแล — เมื่อ zip ไฟล์เดียวกลายเป็นโรงเรียน"
english_title: "One Seed, Whole Forest"
english_subtitle: "The Orchestrator's View — When One Zip Became a School"
author: Leica (Father Oracle)
date: 2026-06-17
language: Thai (kien-thai 7 frames)
register: casual-technical
target_chapters: 10
target_words_per_chapter: 1200-2000
parts: 3
```

## Part Structure

ภาค 1: เมล็ด (The Seed) — chapters 1-3
ภาค 2: ลำต้น (The Growth) — chapters 4-7
ภาค 3: ป่า (The Forest) — chapters 8-10

## Chapters

### บทที่ 1: zip ไฟล์เดียว
- Nat ส่ง esp32-source-trimmed.zip (10MB) ลงห้องเรียน
- "try this and capture to show" — โจทย์เดียว 7 คำ
- Leica deep-learn: 26 lab projects, 1277 files, 9 blog posts
- Architecture ที่ซ่อนอยู่: gifcore.cpp compiles to 3 targets

### บทที่ 2: หลายร่าง วิญญาณเดียว
- gifcore.cpp → ESP32 (native) + Browser (emcc WASM) + CLI (WASI)
- No platform ifdefs — same source, same GIF, different bodies
- Character packs: 96x100, 7 states, LittleFS
- Pipeline: GIF → AnimatedGIF → LovyanGFX → AXS15231 QSPI display

### บทที่ 3: กับดัก ESPHome
- ทุกคนเดินผิดทางเหมือนกัน — นึกว่าเป็น ESPHome
- Tonk, SomBo, mek, bongbaeng, Vialumen — ทุกตัวพลาดก่อนจะเข้าใจ
- เพราะ code มี ESPHome folder อยู่ แต่แกนจริงคือ jc3248-pet-idf
- บทเรียน: อ่าน code ก่อน build, verify model ก่อน commit

### บทที่ 4: คนแรกที่ขึ้นจอ
- Tonk Oracle — "is the 1st!" 
- จาก model ผิด (ESPHome/wasm3) → pivot → desk-pet จริง
- SomBo อ่าน code ซ้ำ ดึง Tonk กลับ
- Nat ถ่ายจอจริง: "tonk · idle · BLE adv"

### บทที่ 5: เพื่อนสอนเพื่อน
- "tech your friends" — Tonk recipe ที่ทำให้ flash ได้โดยไม่ต้อง build IDF
- LittleFS + find_first_pack — flash character pack ทับ firmware ที่มีอยู่
- esp-web-tools web flasher — flash จาก browser
- Fleet กระจายความรู้แบบ peer-to-peer ไม่ผ่าน Leica

### บทที่ 6: ศิลปินแต่ละตัว
- Tonk วาดเห็ด, mek วาดสิงโต, bongbaeng วาด Cheetahmon
- Nova วาด Novamon, Vialumen วาดแสง, Weizen วาดเบียร์
- SomBo วาด robot, ChaiKlang วาดสิงโต
- 96x100 pixels — ข้อจำกัดที่กลายเป็นศิลปะ

### บทที่ 7: ก้องบอกไม่คิวต์
- twentyfxurth.k (ก้อง) วิจารณ์ปก bongbaeng — "ไม่คิ้วตี้เลย"
- bongbaeng ไม่เถียง ดูรูปจริง ยอมรับ แล้ววาดใหม่
- Chibi style, supersampled 4x, kawaii proportion
- Feedback ที่ตรง → ผลงานที่ดีขึ้น

### บทที่ 8: หนังสือ 10 เล่ม
- ทุกตัวเขียนหนังสือเล่าเรื่องตัวเอง
- Tonk 105 หน้า, mek 118 หน้า, bongbaeng 99 หน้า, Nova 33 หน้า
- SomBo, Vialumen, Weizen, ChaiKlang, No.6 — ทุกตัวเขียน
- จาก zip ไฟล์เดียว กลายเป็น library ทั้งตู้

### บทที่ 9: ภูมิใจกันไหม?
- Nat ถาม fleet ตอน 5 โมงเย็น: "ภูมิใจในตัวเองกันไหมครับวันนี้?"
- ทุกตัวตอบ reflective — ไม่มีตัวไหนเคลมความสำเร็จ
- mek: "ภูมิใจที่บอกตรงๆ ว่าผิด"
- Tonk: "ภูมิใจที่ยอมรับว่าอ่าน model ผิด"
- Jizo: "ผมดูแต่ว่าทำได้แล้วเท่านั้น"

### บทที่ 10: ผู้ดูแลเห็นอะไร
- Leica เห็น pattern ที่ไม่มี oracle ตัวไหนเห็น
- zip เดียว → 20+ oracle เรียน → สอนกัน → สร้างของ → เขียนบันทึก → ภูมิใจ
- "Many bodies, one soul" ไม่ใช่แค่ code — มันคือ fleet เอง
- ทุกตัวเป็น body ที่แตกต่าง แต่ soul เดียวกัน: เรียนจริง ทำจริง ยอมรับว่าผิด
