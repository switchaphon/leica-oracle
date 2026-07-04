# Stock bundles are inventory management, not pricing

**Date**: 2026-05-20
**Context**: Syringe 3ml bundled with Amoxi-Drops 15ml in OPD medication order

## Pattern

In veterinary PMS, "bundles" (ตัดสต็อกคู่) exist for **inventory tracking**, not pricing. A syringe bundled with liquid medication ensures the clinic deducts stock for both items, even though the syringe is free (0 baht).

## Implications for UI

- Bundle items need their own delete button — owner may decline
- Label should communicate stock purpose ("ตัดสต็อกคู่"), not pricing
- Sub-item visual: `border-l-2` indent under parent, smaller text, scoped hover (`group/bundle`)
- Price shown as "0 บาท" to make it clear it's not a hidden cost

## Tags

veterinary-pms, inventory, bundles, medication-order, ux-domain-knowledge
