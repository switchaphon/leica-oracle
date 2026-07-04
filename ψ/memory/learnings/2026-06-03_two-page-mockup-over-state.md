# Two-Page Mockup Over Stateful Prototype

**Date**: 2026-06-03
**Source**: OPD paused mode design decision
**Concepts**: prototype, state-management, UX-review, simplicity

## Pattern

When a prototype needs to show two states of the same page (e.g., active vs paused), create two separate page files instead of managing state with localStorage, URL params, or React state.

## Why

- Prototypes are for visual review, not functional testing
- Zero state management = zero bugs from state desync
- Each page is independently linkable (share `/opd` vs `/opd/paused` directly)
- Reviewers can toggle between states by navigating, not by clicking buttons
- Queue QuickDrawer can route to the right page based on sub-state data

## When to Apply

Any time a prototype needs to show multiple states of the same view and someone suggests using client-side state to toggle between them.

## Anti-Pattern

Using localStorage/sessionStorage to persist prototype state across navigations. Adds complexity, creates debugging surface, and the state is invisible to the URL bar.
