# Shared Component = Shared Visual Primitives

**Date**: 2026-05-05
**Source**: PatientHeader extraction session
**Confidence**: High (validated by user feedback + Neon spec)

## Pattern

When extracting a component with multiple variants (full/compact, dense/relaxed), use ONE render function with a density flag — never separate functions that can drift independently.

## Rules

1. **Same primitives across variants**: Both variants must use the same Badge component, same name format, same separator character, same chip component. The flag controls size/visibility, never switches design elements.

2. **Brief agents with ONE adaptive layout**: Describing "Full: use X" and "Compact: use Y" in a brief guarantees inconsistency. Describe one design that adapts via a flag.

3. **Prototype components stay in prototype scope**: Don't put prototype-stage components in production `@/_components/shared/`. Put them in `prototype/{journey}/_components/` — they can graduate later.

4. **Verify visual consistency before presenting**: TypeScript compiling + HTTP 200 proves correctness, not consistency. Take screenshots and compare variants side by side.

5. **Collect all label/text feedback in one batch**: When a component has action buttons with labels, discuss all labels upfront — don't discover corrections one by one across multiple rounds.

## Anti-patterns

- `FullHeader()` and `CompactHeader()` as separate functions → drift guaranteed
- Different chip components for the same data (Badge vs Tag for allergies)
- Different name formats between variants (`name / name` vs `name (name)`)
- Pending timeline steps with action buttons for features that don't exist yet

## Applies to

- Any multi-variant component extraction
- Design system components with size variants
- Cross-page shared components with different density needs
