# CSS-first over Radix Portal in prototype scroll layouts

**Context**: Radix Popover uses Portal (renders to document.body) which breaks positioning in nested scroll containers with `overflow-y: auto`. The calculated y-offset was -446px — completely off-screen.

**Lesson**: In prototype scope with complex scroll hierarchies, use CSS `position: absolute` relative to a parent wrapper instead of Radix Popover/Portal. The inline approach:
- No Portal = no scroll offset miscalculation
- `position: relative` on wrapper + `position: absolute` on dropdown = correct positioning in every scroll context
- Keyboard (Esc) and click-outside handled with tiny event listeners

**When to apply**: Any time a dropdown or popover needs to appear inside a scrollable container with nested `overflow` constraints. Check parent chain for `overflow: hidden/auto/scroll` before reaching for Radix Popover.
