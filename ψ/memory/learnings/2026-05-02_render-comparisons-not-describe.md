# Render Comparisons, Don't Describe Them

**Date**: 2026-05-02
**Source**: SOAP editor slash menu style decision
**Confidence**: High (validated in session)

## Pattern

When choosing between design options (layouts, styles, component variants), create a comparison page that renders all options side-by-side in the actual UI rather than describing differences in chat or listing pros/cons in a table.

## Evidence

Created `/prototype/menu-compare` with 4 menu styles (A/B/C/D) rendered simultaneously. The user scrolled through, compared spacing/typography/icons in context, and chose Style D within minutes. Previous chat-based comparison would have taken multiple rounds of "try this" → screenshot → "no try that."

## When to Apply

- Any time there are 2+ design options for a UI element
- When the user says "ขอดูอีกที" or "เปรียบเทียบ"
- Before implementing a chosen style, let the user see all candidates first

## Connection

Aligns with the pops-clinic-oracle pattern of "prototypes in code via prompts, not Figma-first" (user_role_workflow.md). The comparison page IS the design tool.
