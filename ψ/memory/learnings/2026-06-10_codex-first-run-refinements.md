# Lesson: First real Codex-implementer run — practical refinements

**Date**: 2026-06-10
**Context**: Diagnostic order decoupling (commit a5e758b) — Codex GPT-5.5 implemented 7-file refactor from BRIEF.md in 2 phases (3m04s + 1m40s), zero defects found in lead review
**Source**: live run, pops-clinic + Claude Code lead

## What worked (keep doing)

- **Phase gating in the brief** ("implement Phase 1, STOP, wait") — Codex respected it exactly; lead review between phases caught nothing this time but costs ~1 min
- **Self-check commands inside the brief** (scoped tsc + greps with expected results) — Codex ran them verbatim and reported honestly
- **Exclusive file ownership table** in brief — zero scope creep, `git status` stayed exactly the 7 owned files
- **Lead pre-verification pays**: handover spec'd `chipState` as `'idle'|'selected'|'loading'` but the real type was the `AppointmentChipState` discriminated union — caught while writing the brief, saved a full feedback round-trip

## Traps (avoid next time)

1. **tmux send-keys race**: text + `Enter` in ONE send-keys → Codex TUI eats the Enter, message sits in input box. Fix: send text → `/bin/sleep 1` → separate `tmux send-keys -t {pane} Enter`
2. **Monitor marker false-positives** ×2: the instruction echo contains the marker ("Stop after printing PHASE 1 DONE") AND Codex's acknowledgment paraphrases it ("then stop with PHASE 2 DONE"). Fix: anchor on Codex's final-answer bullet `grep -qE '^• PHASE N DONE'`
3. **Background poll loop** (15s interval, `• Working` idle-detection fallback, 15–20 min timeout, run_in_background) is the right monitor shape — wakes the lead exactly when needed
4. **rtk swallows piped output** sometimes (`git diff | grep` → empty): write to file with `rtk proxy ... > /tmp/x.txt` then Read
5. **Browser UAT catches what component-scoped work can't**: stale guide copy on flow pages still quoted removed hint text + parked "inline form" design — page-level truthfulness is the LEAD's lane, list it in the plan from the start
6. **pnpm-no-lockfile drift**: build broke on a dep present in package.json but absent in node_modules (`react-zoom-pan-pinch`) — when build fails weird, `pnpm install` FIRST, then re-diagnose

## Verdict

Workflow validated on real feature work. Codex = fast, precise, brief-faithful implementer; lead time goes into brief-writing (~15 min incl. verification) + review (~10 min) + UAT. Total feature: ~75 min including 3 WIP commits, browser UAT, and discovering a pre-existing team-side build break.

## Tags

codex, dual-ai, tmux, monitoring, lead-workflow, refinements
