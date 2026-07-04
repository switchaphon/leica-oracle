# Composition via Optional Prop > Extracting a Shared Base

**Date**: 2026-06-03
**Source**: OPD order path refactoring session
**Confidence**: High (validated by implementation + browser verification)

## Pattern

When component A duplicates component B's layout, the simplest fix is:
1. Add an optional prop to B that enables the extra behavior (e.g., `guide?: {...}`)
2. Make A a thin wrapper that calls B with that prop set
3. Delete A's duplicated layout code

Do NOT create a new shared base C that both A and B consume — that's a bigger diff, introduces a new abstraction layer, and achieves the same outcome with more indirection.

## Evidence

`OpdOrderFlowShell` was 100 lines duplicating `OpdPageBody`'s PatientHeader + action buttons + TabsDrawer. Button labels had drifted ("พักคิว" vs "พักการรักษา"). Fix: added `guide` prop to OpdPageBody, reduced shell to 14 lines. Zero new abstractions, zero drift.

## Corollary: Route Axes Should Reflect User Intent

11 per-modality routes (Lab/XRay/US × button/slash/appointment) collapsed to 4 generic routes (order/plan × button/slash). Modality is a modal-selection concern, not a routing concern. Route on intent, modal on detail.

## Corollary: Consolidation > Propagation

You can't have label drift between components if only one component exists. Every "propagate changes to all variants" warning is really "these variants shouldn't exist separately."

## Related

- Reuse Over Rebuild (2026-04-29)
- Shared Component = Shared Visual Primitives (2026-05-05)
- Table Convention Propagation (2026-05-04)
