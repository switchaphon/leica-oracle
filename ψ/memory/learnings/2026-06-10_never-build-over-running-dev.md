# Lesson: Never run `pnpm build` while `pnpm dev` is serving the same `.next/`

**Date**: 2026-06-10
**Context**: Ran production builds 8× during the build-fix loop while Un's dev server was live → dev cache corrupted → **500 on every route**, broke Un's manual UAT mid-session, and made the automated UAT suite fail wholesale (timeouts) — looked like 13 feature bugs, was 1 environment bug.

## Rules

1. Before any `pnpm build` in the vet repo: check `lsof -nP -iTCP:3000 -sTCP:LISTEN`. If dev is running → warn Un / stop dev first, or accept that dev must be restarted after.
2. Recovery: kill `next dev` (+ its `next-server` child), `rm -rf .next`, relaunch — keep it visible in tmux (`tmux new-window -n dev-server 'pnpm dev'` in session 05-pops-clinic).
3. **Pre-warm before browser suites**: curl every route under test until 200 — first-compile on this app exceeds per-test timeouts, and a restarted server makes every route cold.
4. A test that asserts ABSENCE (`toHaveCount(0)`) passes on a broken/blank page — absence checks are only meaningful next to a presence check on the same page.
5. UAT assertions must match the PROTOTYPE's current truth, not the design target: advance confirm still creates PENDING (`buildOrder('DRAFT'|'PENDING')`) — PLANNED-on-confirm is the parked Rev-4 work (TODO: PLANNED order-state UI). Chip shows date·time·vet, never appointmentNo.

## Tags

dev-server, next, build, environment, uat, false-failures
