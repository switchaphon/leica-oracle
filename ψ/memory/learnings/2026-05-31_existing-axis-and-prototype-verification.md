# Learnings — Diagnostic Origin execution + Pet Profile (2026-05-31)

Source: ~7h session executing `DIAGNOSTIC_ORDER_ORIGIN_PRD.md` + building a pet profile base UI. Three reusable lessons.

## 1. A feature's core distinction may already be an axis in the code — forward the existing signal (HIGH)

The "headline feature" (slash `/lab` should know เพิ่ม vs ล่วงหน้า) looked like new state. It wasn't: `DiagnosticContext = 'P_OPD' | 'P_APPT'` **already was** that axis, the SOAP section buttons **already passed** it, and the 3 selectors already threaded it into the built order. The only real defect was that the slash extension **dropped `section`** at one `onCommand` callback boundary. So the build collapsed to: wrap `onCommand` to inject `section`, add an `orderOriginResolver(section)`, and add 3 shared presentational components (tab/chip/popup) wired through one `useOrderMode` hook — instead of three parallel implementations.

**Rule:** before designing new state/storage for a distinction, grep the code for an enum/prop that already encodes it. The cheapest spine forwards an existing signal to the place that drops it. Connects to `2026-05-30_diagnostic-order-origin-patterns.md` (the slash plumbing was "90% wired").

## 2. Verify prototype UX with Playwright CLI click-tests, not just `tsc` (HIGH)

`tsc --noEmit` proved the ~31 files type-checked, but it can't prove behaviour. Short Playwright CLI scripts (`node x.mjs` importing `@playwright/test`, headless, asserting + screenshotting) proved each milestone: O→เพิ่ม / P→ล่วงหน้า, the chip, the confirm popup, and after-close-from-the-profile-header opening the modal with the right pet. It also caught a **Radix `asChild` popover quirk** (synthetic `.click()` didn't open the popover; `.press('Enter')` did) — a real-browser non-issue but a test-harness gotcha worth catching. Pattern: per the project's "no tests for prototypes" rule, these are throwaway verification scripts (`rm` after), not committed tests. CLAUDE.md already says "use Playwright CLI, not MCP" — this is why.

## 3. DS-first = reuse the composite, enhance it backward-compatibly, build-and-flag the gaps (MEDIUM-HIGH)

Un's priority for new UI: **DS → Figma → production** ("and they shouldn't differ much"). Applied to the pet profile: reuse `PatientHeader` (the DS pet-header composite) for the left card; enhance it backward-compatibly (`เปิดแฟ้ม` now renders only when `onOpenProfile` is provided — existing callers unaffected); build the missing pieces (`OwnerCard`, `PetProfileOverview`) and **flag them as DS candidates** rather than silently inventing. Also: the prototype "pet" surface (`/prototype/pet`) was a *list*, not a single-pet profile — **check the actual surface before proposing where a feature lives**. Don't assume a route's name matches its shape.

## 4. PROCESS — offer a handoff on very long sessions before context bloats (MEDIUM)

This ran to ~600K context in one unbroken session. The clean milestone to offer a handover was after the 9 flows; instead it continued into the pet-profile build. On a session this size, proactively propose the cut so the human picks where to split, and so re-reads/cache-misses don't pile up.
