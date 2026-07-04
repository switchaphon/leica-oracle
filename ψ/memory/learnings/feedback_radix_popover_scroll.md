---
name: Radix Popover blocks scroll
description: Radix Popover intercepts mouse wheel events inside dropdown lists — replace with plain positioned div for scrollable content
type: feedback
---

Replace Radix Popover with plain positioned div (absolute + click-outside listener) when the popover content needs to scroll.

**Why:** Radix Popover's DismissableLayer and FocusScope intercept mouse wheel events, making `overflow-y-auto` lists unscrollable with mouse wheel. This broke the "รายการสั่งด่วน" dropdown 3 times before the root cause was found.

**How to apply:** Any scrollable dropdown in `/prototype/` that uses `<Popover>/<PopoverContent>` should use the CategoryPickerInline pattern instead: absolute-positioned div + `useEffect` for click-outside + Escape key. Check all prototype Popovers with scrollable lists.
