---
date: 2026-05-08
source: "session: Un taught prototype folder restructure"
tags: [convention, prototype, folder-structure, ux, workflow]
---

# Prototype Folder Convention: {base-ui}/{activity}

## Structure

```
/prototype/{base-ui}/                   → base page (canonical UI surface)
/prototype/{base-ui}/{activity}/        → sub-prototype forked from base
/prototype/_components/                 → shared generic components across all base-uis
/prototype/{base-ui}/_components/       → domain components owned by that base-ui
```

## 3 Conventions

1. **Component ownership**: Generic UI (PatientHeader, QuickViewDrawer) → `/prototype/_components/`. Domain components (OpdContent, editor, diagnostic) → owned by their base-ui's `_components/`. Cross-domain import is allowed.

2. **Cross-domain import**: Activity pages can import components from another base-ui's `_components/`. E.g. `/queue/call-to-opd/opd/[id]/page.tsx` imports OpdContent from `/opd/_components/`.

3. **Multi-base-ui flows**: Named after the starting base-ui + descriptive activity. E.g. queue → opd → lab → billing = `/queue/full-visit-flow/`.

## Why

- Base page เปลี่ยนที่เดียว → ทุก activity ได้ update (ไม่ต้อง maintain หลาย copy)
- Naming สื่อ relationship: activity เป็น sub-prototype ของ base
- Developer หาง่าย: ดูจาก base-ui folder → เห็นทุก activity ที่เกี่ยว

## Consulted: Neon

Neon reviewed and flagged 3 edge cases (all resolved by convention, no structure change needed).
