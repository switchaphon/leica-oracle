---
name: Prototype infrastructure patterns established
description: Conventions for prototype pages — guide system, handoff viewer, hash URLs, hover tokens, layout control
type: project
---

Patterns established on 2026-05-11 as master template for future prototypes:

**PrototypeGuide**: `data-guide` attributes + `GuideStep[]` array + fixed legend panel (top-right). Badges mark WHERE, panel explains WHAT. Modal-aware filtering hides irrelevant steps. Restart button reloads the flow.

**Handoff viewer**: `/prototype/handoff/[slug]` — centralized viewer with rendered markdown + download. Content stored as TypeScript constants in the viewer page (avoids middleware auth issues with raw `.md` files).

**Hash URLs**: Both `/prototype#opd-order-lab` and `/prototype/design-system#button` support deep-linking. Use `pathToHash()` to convert paths to slugs.

**Hover tokens** (Neon-approved): `--hover-row` (neutral-100), `--hover-nav` (neutral-100/70), `--hover-destructive` (red-50, reserved), `--hover-selected` (brand-light). Border-only hover banned.

**Layout control**: `/prototype` and `/prototype/design-system` and `/prototype/handoff/*` get clean layout (no sidebar/NavBar). All other prototype pages get production sidebar.

**Why:** Consistency across prototype pages. Developer sees the same guide system, handoff format, and hover behavior everywhere.

**How to apply:** New prototype pages follow the `order-lab` template. Add `PrototypeGuide` with steps, populate handoff data in `ALL_PAGES`, create handoff content in the viewer.
