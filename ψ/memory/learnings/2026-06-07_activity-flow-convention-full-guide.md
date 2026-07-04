# Learning: Activity Flow Convention — Full Guide Steps

**Date**: 2026-06-07
**Source**: Un correction during billing-payment page creation
**Confidence**: High (pattern verified across 5+ sibling pages)

## Pattern

Every activity flow page in `/prototype/{domain}/{activity}/page.tsx` must:

1. **Have its own sub-route** — never reuse the base page path
2. **Wrap the parent page** + PrototypeGuide (for modal-based flows like billing, quick-view)
3. **Place `data-guide` attributes** on every interactive element in the flow
4. **Define one PrototypeGuide step per touchpoint** — not just the entry, the full journey
5. **Auto-scroll to the guide target** if it's below the fold (useEffect + 600ms delay)

## Reference implementations

- `queue/call-to-opd/page.tsx` — standalone (870 lines), 1 guide step on row button, `data-guide="call-to-opd-row"` on specific queue item
- `queue/open-quick-view/page.tsx` — thin wrapper (22 lines), 1 guide step on q1 (visible row)
- `opd/order-diagnostic/page.tsx` — shell wrapper (29 lines), **7 guide steps** with data-guide on: open button, mode tab, search, review, confirm, diagnostic block, sidebar accordion
- `queue/billing-payment/page.tsx` — thin wrapper (33 lines), **6 guide steps** with data-guide on: row, items table, confirm, payment tabs, pay, void

## Convention: data-guide inside modals

PrototypeGuide handles `inModal` elements via `el.closest('[role="dialog"]')`. When the billing modal opens, guide badges shift to show inside the modal. Steps that target modal elements (data-guide="billing-confirm-items") become visible only when the modal is open.

## Root cause of the mistake

Jumped to implementation without reading sibling pages. The convention was fully established — 5+ existing activity flows follow it. 2 minutes of reading would have prevented 20 minutes of corrections + 2 rounds of Un's frustration.
