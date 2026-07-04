# Tailwind-Merge Responsive Variant Override

**Date**: 2026-04-29
**Context**: Fixing modal width in pickup-queue-to-opd prototype

## Lesson

`tailwind-merge` treats base utilities and responsive variants as **non-conflicting**. `max-w-[690px]` does NOT override `sm:max-w-[1000px]` — both coexist, and at `sm:` breakpoint the responsive variant wins.

## Rule

To override a responsive utility, **match the breakpoint prefix**:

```
// WRONG — base doesn't override sm:
className='max-w-[690px]'   // won't override sm:max-w-[1000px]

// RIGHT — same breakpoint overrides
className='sm:max-w-[690px]'  // overrides sm:max-w-[1000px]
```

## Also Learned

When overriding styles through a component chain (DialogContent → Modals → StepperModal → page), always read all layers first. Double padding (`p-6` on DialogContent + `px-6` on content wrapper) is easy to miss.

## Tags

tailwind, css, responsive-design, shadcn, dialog
