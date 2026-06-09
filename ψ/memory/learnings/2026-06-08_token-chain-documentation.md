# Documentation works best when written during confusion

**Date**: 2026-06-08
**Source**: rrr: leica-oracle
**Context**: Un felt token switching "doesn't actually switch" — the guide explained setup but not the daily workflow chain

## Pattern

When a user says "it doesn't work" about a multi-step system, the break is always at one specific link in the chain. Effective documentation traces the full chain with each piece's trigger mechanism:

```
pass (stores token) → .envrc (points at token) → direnv (loads on cd) → claude (reads at startup)
```

Each link has a different trigger:
- pass: activated by .envrc calling `pass show`
- .envrc: activated by direnv detecting directory change
- direnv: activated by `cd` (not by file changes in current dir)
- claude: reads token once at startup, never re-reads

## Lesson

Write documentation DURING confusion, not after understanding. The confused person's questions reveal what the docs need to say. A "chain" mental model (A triggers B triggers C) is more useful than listing components side by side.

## Tags

documentation, direnv, token-management, teaching, mental-models
