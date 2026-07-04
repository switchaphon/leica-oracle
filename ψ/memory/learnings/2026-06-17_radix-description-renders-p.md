# Lesson: Radix `*Description` components render a `<p>` — never nest block elements inside

**Date**: 2026-06-17
**Repo**: pops/vet (POPs-Vet frontend)
**Context**: Next.js hydration error `In HTML, <p> cannot be a descendant of <p>` in OPD drug-dose allergy dialog (`DrugDoseSelector.tsx`)

## The Pattern

Radix UI's `AlertDialogDescription`, `DialogDescription` (and the Shadcn wrappers around them) render a `Primitive.p` — i.e. a real `<p>` element. The id of that `<p>` is wired into the dialog's `aria-describedby`.

Therefore: **anything you place inside a `*Description` must be valid inline content.** A child `<p>` or `<div>` produces invalid nesting → React hydration error.

## Wrong

```tsx
<AlertDialogDescription className="space-y-2">
  <p>
    {pet.name_th} มีประวัติแพ้ยากลุ่ม <span className="font-bold">...</span>
  </p>
</AlertDialogDescription>
```

The outer Description is already a `<p>`; the inner `<p>` is both redundant and invalid.

## Right

```tsx
<AlertDialogDescription>
  {pet.name_th} มีประวัติแพ้ยากลุ่ม <span className="font-bold">...</span>
</AlertDialogDescription>
```

Keep contents inline (text + `<span>`). Inline styling spans (`font-bold`, text color) are fine. If you genuinely need a block-level structure, pass `asChild` and render a single `<div>` yourself instead of letting it emit a `<p>`.

`space-y-2` (vertical gap between block children) is meaningless once the children are inline — drop it.

## Generalizable Rules

1. When a Radix/Shadcn primitive's name maps to a semantic HTML element (`Description` → `<p>`, `Title` → `<h2>`), treat its allowed children by that element's content model.
2. When a user's status claim ("fixed", "done") contradicts the file, verify the file first — the code is the source of truth.
3. Nested-`<p>` bugs cluster: after fixing one, grep the file for other `*Description` elements and stray `<p>` to catch siblings.
