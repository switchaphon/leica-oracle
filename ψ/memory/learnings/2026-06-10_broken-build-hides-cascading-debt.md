# Lesson: A build broken at an early phase hides ALL later-phase debt

**Date**: 2026-06-10
**Context**: Fixing the generic_drugs build break (commits e00f2eb + 13423c1) took 8 build iterations — each fix revealed the next layer
**Source**: live session, pops-clinic

## The cascade (what one webpack error was hiding)

`next build` phases run in order: webpack compile → ESLint → type-check → static generation. A failure in an early phase means NOTHING after it has run since the break began (Jun 8, commit 3cc7c36). Unblocking layer 1 revealed, in sequence: 17 lint errors → public/ static data in type-check scope (TS2590) → missing required prop in a route page → missing PLANNED in 3 of OUR status maps → dead status comparisons. Every one had been committed blind because gotcha #6 (no CI on MRs) + broken local builds = zero feedback.

## Lessons

1. **When inheriting a "broken build", budget for an onion, not a bug** — state each layer plainly and keep peeling; don't promise green after the first fix.
2. **`tsc --noEmit` once >> rebuild N times** — after the second type error, run full tsc to see the whole remaining queue (but filter: next build skips `.test.` / `_test_` / `__mocks__` paths, so those tsc errors don't block builds).
3. **`git check-ignore -v <path>`** is the instant answer to "why was this file never committed" — here `.gitignore` had a blanket `/docs` ignore that silently dropped the author's generated data.
4. **rtk wrapper gotcha**: bare `grep` gets rewritten to `rtk grep` (compact/truncated output, garbles multi-file searches). For exact output: `/usr/bin/grep` or write to file + Read. (Extends the known ls/cat issue.)
5. **eslint bans @ts-nocheck** (`ban-ts-comment`) — pair with `/* eslint-disable @typescript-eslint/ban-ts-comment */` when nochecking a generated data file.
6. After OUR features merge while the build is red, **re-run a green build before claiming feature debt-free** — PLANNED status maps from our own 9115a1c were missing and invisible.

## Tags

build, ci, type-debt, gitignore, rtk, onion-debugging
