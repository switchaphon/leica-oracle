# React State Updater Side Effects

**Date**: 2026-05-19  
**Source**: X-ray order extremity delete crash  
**Tags**: react, state-management, anti-pattern

## Pattern

Never call a state setter (e.g. `toggleRegion`) inside another state setter's updater function (e.g. `setExtSites(prev => ...)`). React strict mode can re-invoke the updater, and side effects from the first invocation may corrupt the second.

## Bad

```tsx
setExtSites((prev) => {
  const np = { ...prev }; delete np[siteCode];
  if (Object.keys(np).length === 0) toggleRegion('EXTREMITY'); // side effect!
  return np;
});
```

## Good

```tsx
let willBeEmpty = false;
setExtSites((prev) => {
  const site = prev[siteCode];
  if (!site) return prev; // guard against re-invocation
  const np = { ...prev }; delete np[siteCode];
  willBeEmpty = Object.keys(np).length === 0;
  return np;
});
if (willBeEmpty) toggleRegion('EXTREMITY'); // outside updater
```

## Key Points

- The updater function runs synchronously before `setState` returns, so the closure variable (`willBeEmpty`) is set by the time you check it
- Always add a guard (`if (!site) return prev`) for the case where the updater is re-invoked with already-modified state
- This applies to any cross-state coordination, not just this specific case
