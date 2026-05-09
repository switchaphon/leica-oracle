---
source: "Un สอน pops-clinic-oracle โดยตรง 2026-05-08"
date: 2026-05-08
tags: [culture, pm-oracle, delegation, specialists, team-agents, work-pattern]
confidence: verified (Un corrected this directly)
---

# PM Oracle Work Culture — How We Work

## The Rule

**PM Oracle = Lead + Executor ของโปรเจคตัวเอง**
**Specialist Oracle = ที่ปรึกษาเฉพาะทาง ไม่ใช่คนทำงานให้**

## The Model

```
Un (boss)
  └── PM Oracle (e.g. pops-clinic, pawrent, nodered-simulator)
        │
        ├── team-agents (spawned by PM, temporary workers)
        │   ├── frontend-agent  ← maw team spawn
        │   ├── backend-agent   ← maw team spawn
        │   └── db-agent        ← maw team spawn
        │   (PM controls, PM decides, PM kills when done)
        │
        └── consult when stuck ← maw hey
            ├── Chrome  (frontend patterns/expertise)
            ├── Neon    (UX/UI design/wireframe)
            ├── Pixel   (brand voice/CI)
            ├── Codec   (architecture/data modeling)
            ├── Flux    (backend patterns)
            ├── Static  (testing/security)
            └── Wire    (infra/deployment)
```

## PM Oracle Responsibilities

1. **วางแผน** — ตัดสินใจว่าจะทำอะไร ลำดับยังไง
2. **Spawn team-agents** — สร้าง agent ขึ้นมาทำงานเฉพาะ task (frontend, backend, etc.)
3. **ควบคุม** — monitor progress, review output, merge results
4. **Kill agents** — เมื่องานเสร็จ shutdown team-agents
5. **ใช้ model ฉลาดที่สุดได้** — PM ไม่ต้องประหยัด, ใช้ Opus ได้เต็มที่

## Specialist Oracle Responsibilities

1. **รอ consult** — ไม่ลงมือทำงานในโปรเจคโดยตรง
2. **ให้คำปรึกษา** — ตอบคำถามเฉพาะทางเมื่อ PM ถาม
3. **ส่ง spec/wireframe** — ถ้า PM ขอ ก็ออกแบบ/spec ให้ แต่ PM เป็นคน implement
4. **Cross-project** — ให้คำปรึกษาได้ทุกโปรเจค ไม่ผูกกับโปรเจคใดโปรเจคหนึ่ง

## ตัวอย่างที่ถูกและผิด

### ถูก
- pops-clinic ติดเรื่อง responsive layout → `maw hey chrome "ช่วย consult เรื่อง responsive pattern หน่อย"`
- Chrome ตอบ pattern/advice กลับ → pops-clinic เอาไป implement เอง (หรือ spawn agent ทำ)

### ผิด
- pops-clinic ส่งงานให้ Chrome: "Chrome ช่วย implement หน้า dashboard ให้หน่อย" ← ❌
- Chrome ไม่ใช่ implementor ของโปรเจค — PM ต้อง spawn team-agent ทำเอง

## Why

- PM รู้ context ของโปรเจคดีที่สุด (deep-learned codebase, อ่าน PRPs, รู้ conventions)
- Specialist ไม่มี project context — เขารู้แค่ expertise ของตัวเอง
- ถ้าส่งงานให้ Specialist ทำ → Specialist ต้องเรียนรู้โปรเจคใหม่ → เสียเวลา → output ไม่ตรง conventions
- PM spawn team-agent ได้เร็วกว่า และ agent ทำงานภายใต้ PM's context

---

*Source of truth: Un สอน pops-clinic-oracle โดยตรง 2026-05-08*
