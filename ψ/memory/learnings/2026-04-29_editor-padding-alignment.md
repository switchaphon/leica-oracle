# Lesson: Editor padding alignment — match content to editor, not the reverse

**Date**: 2026-04-29
**Context**: Prototype OPD page with tiptap NotionEditor

## Pattern

When a rich text editor has built-in left padding for UI affordances (block handles, line numbers, gutter icons), don't remove that padding to align with surrounding content. Instead, add matching padding to the surrounding content.

## Why

- The editor's padding exists to house interactive elements (drag handles, add-block buttons) that need hover space
- Removing it (`!pl-0`) breaks those affordances — handles overlap text
- Adding `pl-10` to body text paragraphs aligns everything without breaking anything

## Implementation

```tsx
const BODY_INDENT = 'pl-10'; // matches NotionEditor's built-in pl-10

<SoapBlock>
  <p className={`text-sm ${BODY_INDENT}`}>Chief Complaint: ...</p>
  <p className={`text-sm text-slate-400 ${BODY_INDENT}`}>Placeholder...</p>
  <NotionEditor ... /> {/* has its own pl-10 */}
</SoapBlock>
```

## Tags

tiptap, alignment, padding, NotionEditor, block-handle, UI-affordance
