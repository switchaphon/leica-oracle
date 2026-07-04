# Design System Must Render — Docs Aren't Enough

**Date**: 2026-05-04
**Context**: User couldn't evaluate design tokens from DESIGN_SYSTEM.md alone
**Confidence**: HIGH

## The Pattern

A markdown design system spec (hex codes, token names, usage rules) is necessary for AI agents and developers but insufficient for designers. The moment of understanding happens when tokens render as actual pixels in a browser.

**Always build both:**
1. **Spec file** (DESIGN_SYSTEM.md) — AI-readable, copy-pasteable tokens, comprehensive rules
2. **Visual reference** (/prototype/design-system) — interactive, rendered, same Tailwind config as production

**The visual reference must:**
- Use the SAME CSS config as the production app (not a standalone HTML with hardcoded values)
- Show components in ALL states (default, hover, focus, disabled, error, loading)
- Allow interactive property changes (sliders, toggles) with instant re-render
- Display the dev spec (Tailwind classes, CSS values) alongside each visual

**For the framework choice:**
- Next.js prototype page > Storybook for token visualization (Storybook is component-first, not token-first)
- Keep Storybook for component isolation with prop controls
- Don't use standalone HTML — it drifts from the real config immediately

## Anti-Pattern
Writing a comprehensive token doc and calling the design system "done" without rendering it. The user said "ผมเห็น markdown มันเหมือนต้องมาเปิดไฟล์อ่าน แล้วมันไม่เห็นรูปร่างหน้าตาจริง ๆ"
