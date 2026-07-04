# Lesson: PrototypeGuide Beacons Require Visible DOM Anchors

**Date**: 2026-06-03
**Context**: OPD diagnostic flow slash pages had zero visible guide beacons
**Tags**: prototype, guide, beacon, data-guide, UX, SOAPContent

## Pattern

The `PrototypeGuide` component renders numbered beacon circles at DOM elements matching `data-guide` selectors. It checks `getBoundingClientRect()` and only renders beacons for elements with `height > 0` and `top > 0` within the viewport.

**Consequence**: Guide steps whose selectors point to elements inside unopened modals/dialogs produce zero beacons on page load. The legend panel appears empty and the bottom bar title has no corresponding callouts.

## Rule

Every guide config must include **at least one step** whose selector matches a **visible-on-load** element. For flows triggered from within SOAP sections:

- `[data-guide="objective-editor"]` — visible in the Objective SoapBlock
- `[data-guide="plan-editor"]` — visible in the Plan SoapBlock
- `[data-guide="order-lab-open"]` — visible button in Objective actions
- `[data-guide="order-advance-open"]` — visible button in Plan actions

Modal-internal selectors (`order-mode-tab`, `lab-search`, `lab-confirm`, `xray-anatomy`, `us-search`) only become visible after the modal opens — use them for step 2+ but never as the only steps.

## Anti-Pattern

```typescript
// BAD: all selectors inside modal — zero beacons on page load
steps: [
  { selector: '[data-guide="order-mode-tab"]', label: '...', step: 1 },
  { selector: '[data-guide="lab-search"]', label: '...', step: 2 },
]

// GOOD: first step on visible element, rest in modal
steps: [
  { selector: '[data-guide="objective-editor"]', label: '...', step: 1 },
  { selector: '[data-guide="order-mode-tab"]', label: '...', step: 2 },
  { selector: '[data-guide="lab-search"]', label: '...', step: 3 },
]
```
