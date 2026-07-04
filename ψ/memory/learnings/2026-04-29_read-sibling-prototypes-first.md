# Read sibling prototypes before building new ones

**Date**: 2026-04-29
**Source**: pickup-queue-to-opd prototype session
**Context**: Built queue page from scratch, user rejected it because it didn't match existing diagnostic-request-list prototype visual pattern

## Pattern

Before building any new page under `src/app/prototype/`, always read existing prototypes in the same directory first. The visual conventions (Card layout, FilterChip, Table styling, pagination) must be consistent across all prototypes — they are siblings, not independent apps.

## Anti-pattern

Reading production code (QueueStatBox, QueueTable) and trying to approximate Figma. Production components have different visual weight and structure from the prototype convention.

## Rule

1. `ls src/app/prototype/` — see what exists
2. Read the most recent prototype page.tsx completely
3. Copy its structural patterns: Card layout, filter bar, table wrapper, pagination
4. Only then adapt the content (columns, data, actions) for the new feature
