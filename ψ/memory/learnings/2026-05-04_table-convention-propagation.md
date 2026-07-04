# Lesson: Table conventions are contracts — propagate, don't vary

**Date**: 2026-05-04
**Source**: Dashboard/Queue/Pickup table alignment session
**Severity**: High — caused ~2 hours of rework

## Pattern

When multiple prototype pages share the same table structure (queue data), the table implementation must be identical: same column order, same widths, same overflow behavior, same shared components, same icon mapping, same responsive breakpoints.

## Anti-pattern

Building each page's table independently, even from the same data shape, leads to:
- Different column headers ("สัตว์" vs "สัตว์เลี้ยง")
- Different icons (PawPrint vs Dog, ArrowDownUp vs ArrowUpDown)
- Different spacing (mb-0.5 vs mt-2, text-gray-500 vs text-gray-400)
- Different button styles (text buttons vs icon buttons, green vs gray)
- Different filter bar patterns (FilterChip vs FilterDropdown, bordered vs text-brand reset)
- Different HN formats (#00001 vs HN66-10-001)

## Rule

1. One table convention = one source of truth (dashboard is now canonical)
2. New pages clone the canonical table, change only business logic
3. Column widths, overflow rules, icon buttons, responsive behavior travel together as a unit
4. Any change to the table convention must propagate to ALL pages in the same commit

## Tags

prototype, table, convention, consistency, clone-dont-create
