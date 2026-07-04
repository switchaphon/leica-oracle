# Lesson: Prototype UI label conventions

**Date**: 2026-06-15
**Context**: pops/vet prototype index (`src/app/prototype/page.tsx`)

## Pattern

Use plain-language labels on prototype-facing UI, not internal product jargon.

- "PRD" → "Document" (self-explanatory to any reader)
- "Appointment Page" → "Open Prototype" (describes the action, not the destination)

## Tailwind: right-align single element in flex row

Wrap the element in `<div className="ml-auto">` rather than adding `justify-between` to the parent — this preserves the left-side alignment and works correctly when the element is conditionally rendered.

```tsx
<div className='flex items-center gap-3'>
  <Icon />
  <Title />
  <Chip />
  <div className='ml-auto'>
    {condition && <Button />}
  </div>
</div>
```

## Context compaction signal

When a session ends mid-verification (user's first message is "done?"), it means the previous session closed without a browser check. Future sessions: prompt for browser verification before the session ends, not after.
