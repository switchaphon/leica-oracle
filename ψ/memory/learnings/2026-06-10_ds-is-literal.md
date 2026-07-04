---
name: ds-is-literal
description: "ไปดูใน design-system" means open the DS page, read exact classes, match them — never approximate from memory
metadata:
  type: feedback
---

When Un says to follow the design system (e.g. "ให้เป็นไปตาม design-system#tabs"), they mean pixel-exact match. Read the DS page source, extract the exact Tailwind classes, and use them. Don't reconstruct from what you remember the DS looked like.

**Why:** Un caught font-weight (font-medium vs font-normal on inactive tabs), button variant (text link vs Button outline), and layout (arrow vs justify-between) — all because I approximated instead of copying the DS spec.

**How to apply:** Before implementing any DS-referenced change: 1) Read the DS page.tsx section, 2) Extract exact class strings, 3) Apply them verbatim. If the shadcn component has built-in styles that conflict, override explicitly.

Related: [[grep-before-edit]]
