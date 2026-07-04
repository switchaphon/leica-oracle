# Lesson: First Codex Day — synthesis of the lead-implementer loop (deep retro)

**Date**: 2026-06-10
**Context**: /rrr --deep synthesis over the whole day: decouple feature + build fix + dual-track UAT. Details live in the 4 per-incident learnings of today; this file is the cross-cutting view with confidence levels.
**Source**: rrr --deep: pops-clinic-oracle

## The loop that now works here (HIGH confidence, 2/2 dispatches zero-defect)

```
verify spec against code → BRIEF.md (ownership table + phases + embedded self-checks)
→ tmux pane + codex → send text, sleep 1, separate Enter
→ background monitor (15s poll, anchor ^• PHASE N DONE, idle fallback)
→ lead reviews ACTUAL DIFF between phases → changelogs by lead → browser UAT → commit with Un's approval
```

Lead time ≈ brief 15 min + review 10 min + UAT. Implementer wall-clock ≈ 5 min/feature. The brief is a self-enforcing contract: Codex ran every embedded self-check verbatim and reported honestly, including the check that "failed" semantically (grep exit 1 = clean).

## Cross-cutting insights

1. **Feedback-starved systems compound debt silently** (HIGH) — no CI on MRs + red local build since Jun 8 = 7 layers of invisible debt, 2 of them OURS (PLANNED maps from 9115a1c). The fix discipline: after ANY period of red builds, full `tsc --noEmit` + green build before claiming any feature area clean.
2. **Two kinds of false test failures, same root** (HIGH) — environment lies (corrupted dev server → 13 "failures") and design-memory lies (asserting PLANNED-on-confirm / appointmentNo that the prototype never had). Both fixed by the same rule: **assert from the code's current truth, verified the same way briefs are.**
3. **Handovers decay against a moving tree** (MEDIUM-HIGH) — today's handover had a stale batch plan (unbuildable) and one wrong type within 1.5 hours of writing. Handovers should stamp "verified against tree at HH:MM" and leads must re-verify before briefing.
4. **The role shift is real** (HIGH) — PM-lead now means: verify → contract → dispatch → review → UAT → own the env. I wrote ~30 lines of production-adjacent code today by hand (lint/type fixes); everything else was contracts, reviews, and verification. This matches "PM owns execution, specialists consult" from May 8 — Codex slots in as the execution tier below team-agents.
5. **Environment ownership is part of the lead job** (HIGH) — I broke Un's manual UAT by building over the live dev `.next`. The lead who dispatches verification must also guarantee the verification environment.

## Connections to standing threads

- UAT-04 finding makes **TODO: PLANNED order-state UI** concrete: `buildOrder('DRAFT'|'PENDING')` is the exact seam where Rev-4's DRAFT→PLANNED lands. Grill-ready.
- Appointment-binding feedback loop (created appointment → chip selection) is the next UX decision on this surface — modal currently fires blind.
- Extends [[codex-workflow]] + the 4 today-learnings: codex-implementer-claude-lead-workflow, codex-first-run-refinements, broken-build-hides-cascading-debt, never-build-over-running-dev.

## Tags

codex, lead-workflow, synthesis, build-discipline, uat, environment, deep-retro
