---
title: tailwind-merge treats base utilities and responsive variants as non-conflicting.
tags: [tailwind, css, responsive-design, shadcn, tailwind-merge]
created: 2026-04-29
source: rrr: pops/app/vet
project: github.com/nicekid1/pops-vet
---

# tailwind-merge treats base utilities and responsive variants as non-conflicting.

tailwind-merge treats base utilities and responsive variants as non-conflicting. `max-w-[690px]` does NOT override `sm:max-w-[1000px]` — both coexist, and at sm: breakpoint the responsive variant wins. To override, match the breakpoint prefix: use `sm:max-w-[690px]` to override `sm:max-w-[1000px]`. Always read the full component chain (DialogContent → Modals → StepperModal → page) before writing className overrides.

---
*Added via Oracle Learn*
