# Enrichment-Then-Inject Pattern for Shared Components

**Date**: 2026-06-02
**Context**: Queue timeline modals — injecting page-specific actions into shared QuickViewDrawer
**Confidence**: High (proven in production, 22/22 tests)

## Pattern

When a shared component (QuickViewDrawer, TimelineStep) renders data with action slots (`onAction?: () => void`) but the page needs to control what those actions do:

1. **Clone** the data in a `useMemo` at the page level
2. **Match** on a stable key (e.g., `action.label` string)
3. **Inject** callbacks that set page-level state (modal open, navigation, etc.)
4. **Pass** the enriched data to the shared component

```typescript
const enrichedQueue = useMemo(() => {
  if (!selectedQueue) return null;
  return {
    ...selectedQueue,
    status_history: selectedQueue.status_history?.map(step => {
      if (!step.action) return step;
      const enriched = { ...step };
      if (step.action.label === 'ดูใบแจ้งหนี้') {
        enriched.onAction = () => { setData(lookup[id]); setOpen(true); };
      }
      return enriched;
    }),
  };
}, [selectedQueue]);
```

## Why This Works

- **Zero changes to shared components** — QuickViewDrawer and TimelineStep stay untouched
- **Inversion of control** — the page decides behavior, not the component
- **Type-safe** — onAction is already optional on the interface
- **Composable** — different pages can inject different actions for the same data shape

## When to Use

- Shared component has action/callback slots in its data interface
- Page needs context-specific behavior (open a specific modal, navigate to a specific route)
- Multiple pages use the same component with different action meanings

## Watch Out

- Mock/data interfaces must include the callback field (`onAction?: () => void`) even if mock data never provides it
- String matching on `action.label` is fragile — consider an `action.type` enum for production code
- The enriched object must remain structurally compatible with the component's expected type

## Prior Art

Same pattern used in DiagnosticQuickViewDrawer (lines 477-478): `timeline[0].onAction = () => setOrderModalOpen(true)` — but done inside the drawer component itself, not at page level. The page-level approach is cleaner when the component is truly shared.
