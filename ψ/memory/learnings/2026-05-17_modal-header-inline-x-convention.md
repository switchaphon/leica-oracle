---
name: Modal header inline X convention
description: Always use hideCloseButton + inline X in header flex row for custom modal headers — avoids absolute positioning alignment issues with title and chips
type: learning
date: 2026-05-17
source: rrr --deep
---

Shadcn Dialog's default close button uses `absolute right-4 top-4` which doesn't align with flex row content (title text gets pushed down by taller chips due to `items-center`). Standard convention:

```tsx
<DialogContent hideCloseButton className='...'>
  <div className='px-6 pt-4 pb-3 border-b'>
    <div className='flex items-center gap-2'>
      <DialogTitle>Title</DialogTitle>
      {/* chips, badges */}
      <div className='flex-1' />
      <button onClick={onClose}>
        <X className='h-4 w-4' />
      </button>
    </div>
  </div>
```

Benefits:
- X naturally aligns with title and chips via flexbox
- No `pr-10` padding hack needed
- Close handler wired to parent state (not radix default)
- Works with any header height

Applied to: DiagnosticQuickViewDrawer OrderDetailModal, LabTestSelector.
