# min-height creates visual gap illusion

**Date**: 2026-05-20
**Context**: OPD SOAP editor → inline block spacing

## Pattern

When a container has `min-height` and variable content, the CSS margin between elements stays constant but the **perceived visual gap** varies:

- Full content → content bottom is near container bottom → margin = visual gap
- Sparse content → content bottom is far from container bottom → unused space + margin = larger visual gap

## Fix

Override `min-height: 0` in context-specific CSS (e.g., `prototype-editor.css`) so the container shrinks to fit content exactly. The structural margin then becomes the only source of visual gap, making spacing consistent regardless of content volume.

## Rule

Never diagnose spacing issues by reading CSS alone. Measure rendered pixels with dev tools. Equal `margin-top` values produce unequal visual gaps when parent containers have `min-height`.

## Tags

css, spacing, min-height, visual-perception, tiptap, editor
