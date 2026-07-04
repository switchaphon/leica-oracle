# Dropdown Taxonomy + Audit-First Pattern

**Date**: 2026-05-11
**Context**: DS dropdown system design, repeated corrections from user
**Confidence**: High (validated through multiple iterations)

## Dropdown Taxonomy (4 Types)

| Type | Primitive | Trigger | Selected State |
|------|-----------|---------|----------------|
| A. Single Select | shadcn Select | rounded-lg h-9 | Pink row bg `bg-[#FFF0F7]` + text `text-[#E5007D]` + Check icon |
| B. Multi-Filter | Popover + Checkbox | rounded-full pill | Pink checkbox only (`data-[state=checked]:border-[#E5007D] data-[state=checked]:bg-[#E5007D]`), row stays normal |
| C. Action Menu | DropdownMenu | DS Button (gradient for Create CTA) | No selection state — actions fire once |
| D. Contextual Picker | DarkPill + Popover | rounded-md h-6 bg-zinc-900 | Same as C — no persistent selection |

**Decision tree**: Single value persists in trigger → A. Narrow dataset → B. Trigger action → C. Dense clinical UI → D.

**Shared panel tokens**: w-56, p-1 wrapper, shadow-md, rounded-lg, 4px gap from trigger.
**Shared item tokens**: hover:bg-neutral-100, rounded-md, text-sm, text-neutral-600.

## Audit-First Rule

When designing a DS pattern that already exists in live components:
1. Find the live component first (grep/screenshot)
2. Match its behavior exactly in the DS mock
3. Only THEN propose changes if the live pattern is wrong

Never invent a DS mock style that contradicts a working live component without explicit user approval. The live code is the ground truth; the DS documents it, not the other way around.

## The สร้างใหม่ Rule

Page-level Create CTA = brand gradient (`linear-gradient(135deg, #E5007D → #FF6B35)`). This is Type C Action Menu with DropdownMenu primitive. Never use default Button variant for this — the gradient is brand identity.
