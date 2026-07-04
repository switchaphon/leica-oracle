---
date: 2026-05-23
source: "rrr --deep: pops-clinic-oracle"
concepts: [taxonomy, be-spec, figma-rtd, source-of-truth, grill, data-model]
---

# Check BE Spec Before Grilling UI Taxonomy

When designing a data taxonomy (service types, status enums, category systems), always ask: "is there an existing BE specification?" before grilling from UI artifacts alone.

We grilled 13 questions against RTD Figma and arrived at a clean 3-type model. Then the BE SOT document (POPS-257) arrived with different hex colors, different Thai labels, and 14 subtypes (including IPD/LAB/BOARDING/HOTEL that we'd explicitly excluded).

The grill wasn't wasted — the UX decisions (IPD inherits parent color, Lab is an order) are valid display logic. But the data model must align with what the API returns. Prototype mock data should match BE enum values, even if the UI treats some values differently (e.g., filtering IPD out of the daily queue list).

**Rule**: Grill against BOTH Figma design AND BE specification. If only one exists, flag the gap before implementing.
