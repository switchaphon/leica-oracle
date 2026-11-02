# Handoff: Codex pilot has 4 clean WPs, next is widen-or-hold (Opus leads, Codex works)

**Date**: 2026-11-02 18:45
**Context**: nearly full
**Branch**: `feat/codex-seat` (5 commits, not pushed; main untouched at 1a1541e)

## What We Did

- Un re-subscribed to Codex today. Verified by running it, not by reading config: `codex exec` works headless; one weekly quota
  window and no credits, resets Mon 09 Nov 15:01 GMT+7; the tier was confirmed by Un. The "no Codex" memories of 2026-10-18 are superseded
  (history kept inside them).
- omx answer for Un: installed (v0.18.13) and runs, but its setup is gone from `~/.codex` (`omx doctor`: 12 ok, 5 warnings). `omx exec` equals
  `codex exec` today. Not in the main flow. Un then said "ok ลอง" and the pilot started.
- Built `codex-wp` (stdlib Python), test first, 102 unit tests, 12 injected bugs all caught, selftest PASS on CLI 0.166.0:
  - 6c47c5f v0.1.0 tool + learnings note
  - 283ba94 v0.1.1 selftest record and `selftest WARN` in `check` when the CLI or model changed (the CLI was upgraded 0.144.1 -> 0.166.0 at 16:36 by someone unknown)
  - 183b863 v0.1.2 `follow` (read-only live view for a tmux pane), `--tdd` now runs `--setup` in the base worktree and says why it is red, `done` ignores symlinks and junk (all from pops-658's notes)
  - e5369e2 v0.1.3 preamble rule 6 fixed (it pushed the worker to hide files it could not delete), WP field `Ignore:`, `run --follow` auto-on when stdout is a terminal (from pops-655)
  - Installed atomically as `~/.claude/bin/codex-wp` (v0.1.3).
- 05f4430 /learn of maw-codex-team-kit: it cannot run on the installed maw-rs (a native `codex` command shadows a plugin of that name), nothing to adopt.
- agent-team skill (outside git): `scripts/dispatch_external.sh` is now a shim for codex-wp (original kept as `.orig-2026-11-02`); `references/templates.md` has a "Codex seat" section.
- Pilot in pops-vet-oracle: wrote the letter to its `ψ/inbox/` and sent SendMessage to the live windows `pops-655` and `pops-658`; Un confirmed in both windows. I did not edit their CLAUDE.md or memory.
  By 18:45 pops-vet had changed its own CLAUDE.md (+14 lines, "Codex is back" appears twice) and its memory file. I did not read what it wrote.
- Pilot results, read from `~/.codex-wp/runs/*/meta.json` (all PASS, 0 violations, 0 committed junk, 0 worker commits, red test first):
  - `20261102-165532-pops-658-handoff-tables--0c0e` 78.9 s, in 212k (cached 180k) out 4.5k, 13 files
  - `20261102-170236-pure-helpers-of-the-hand-a01a` (pops-655) 80.8 s, in 308k (cached 249k) out 5.0k, 5 files
  - `20261102-172030-pops-658-job-tables-chec-5c59` 29.2 s, in 142k (cached 121k) out 2.8k, 2 files
  - `20261102-183845-pops-658-job-tables-walk-f7f2` 44.4 s, in 213k (cached 168k) out 3.3k, 2 files
  - Lead review (pops-655) still found two quality points the mechanical checks cannot see (a constant reused for a different rule; error messages without the bad value). The lead fixed them red first (its commit 9189752, branch feat/POPS-655-handoff-library). pops-658 reported 96 Postgres tests green and 6 deliberate breaks caught (unverified by me).
  - Quota meter still reads 0.0% after about 1.5M input tokens (86% cached) across 9 runs including selftests, so one WP is far below its resolution.

## Pending

- [ ] Pilot gate reached (criterion was 2-3 clean WPs; there are 4, across two repos). Widening is Un's call, not mine.
- [ ] Letter to the other 14 sons, after Un agrees to widen.
- [ ] `/dig --codex` (dig.py reads only `~/.claude/projects`, so it cannot see Codex sessions).
- [ ] omx as an optional second layer, only if Un wants it (needs a decision on `omx setup`: user scope writes into the ChatGPT app's `~/.codex`).
- [ ] maw-rs upgrade (installed alpha.1027, newest alpha.2316 of 2026-09-12). Not started; a separate decision.
- [ ] `codex-wp` allowlist in the sons' permission settings at rollout; `~/.claude/bin/codex-wp.bak-*` backups accumulate (harmless).

## Next Session

1. `~/.claude/bin/codex-wp check`. A `selftest WARN` line means the CLI or model changed: run `codex-wp selftest` before any other step. Then `codex-wp status`.
2. Read the new runs' numbers only (`~/.codex-wp/runs/*/meta.json`: status, tokens, violations, revise rounds). Do not read the pilot repos' diffs; that is the leads' job.
3. Bring Un this one decision with the numbers above: widen from POPS-655/658 to the other implementation windows in tmux `04-pops-vet`, same rules, or hold. His words: "04-pops-vet มีงาน implement เยอะมาก".
4. Ask Un the open questions below (skills, CLI upgrader, push or merge of `feat/codex-seat`, the outbox letter).
5. After a yes to widen: DNA letter to the other 14 sons (file in their `ψ/inbox/` plus SendMessage to live windows, same pattern: "ask Un in your own window first"). The stale beliefs live in: rpro-ent (`feedback_delegate_execution_to_codex.md` says SUSPENDED 10-07, `feedback_codex_team_must_use_omx.md`), vets-hub (`feedback_agent-routing-codex-vs-claude.md`, codex-first with no suspension note); twelve sons hold no Codex memory. Let the sons update themselves.
6. Then `/dig --codex`.

## Key Files

- `~/.claude/bin/codex-wp` (v0.1.3). Source, tests and README: `ψ/lab/codex-wp/` (`codex_wp.py`, `test_codex_wp.py`, `README.md`, `install.sh`) on `feat/codex-seat`. State: `~/.codex-wp/{runs,worktrees,slots,selftest.json}`.
- `~/.claude/skills/agent-team/scripts/dispatch_external.sh` (shim), `~/.claude/skills/agent-team/references/templates.md`.
- `ψ/memory/learnings/2026-11-02_codex-seat-built.md`; `ψ/learn/Soul-Brews-Studio/maw-codex-team-kit/` (hub plus three documents); `ψ/learn/.origins` (+1 line).
- `ψ/outbox/2026-11-02_to-pops-vet_codex-is-back-pilot-655-658.md` (untracked, see below). The delivered copy is in `pops-vet-oracle/ψ/inbox/2026-11-02_from-leica_codex-is-back-pilot-655-658.md` (untracked in that repo, like Leica's earlier letters there).
- Leica memory (outside git, `~/.claude/projects/-Users-switchaphon-ghq-github-com-switchaphon-leica-oracle/memory/`): `codex_resubscribed_2026-11-02.md` (the running log), plus the revived `codex_vs_claude_decision_tree.md` and `oracle_follows_decision_tree.md`, and banners in `maw_codex_team_kit.md`, `codex_team_lifecycle.md`, `codex_agents_deployed.md`.

## Still Running or Waiting

- Nothing of mine is running. The live pilot windows are `pops-655` and `pops-658` in tmux `04-pops-vet`; my last messages to both were delivered, no reply since.
- Waiting on Un: the four decisions under Open Questions.

## Uncommitted WIP

- `ψ/outbox/2026-11-02_to-pops-vet_codex-is-back-pilot-655-658.md` in leica-oracle (untracked on purpose: the repo is PUBLIC and the letter names tickets and project directories). Decide: commit, stash or discard.

## Decisions Locked

- Un: pilot = pops-vet with POPS-655 and POPS-658; the 2026-07-29 rule "Opus writes the code" is lifted for that oracle; "ok ลอง เพราะตอนนี้งานของ 04-pops-vet มีงาน implement เยอะมาก".
- Un: Leica's first scope was only `~/.claude/bin`, the agent-team skill and Leica's own `ψ/`. Sons were touched only after he said go, and only by letter and message, never by editing their CLAUDE.md or memory.
- Design: exec-first (`codex exec` through codex-wp), no omx, no `maw team`, no bypass flag. The lead reads the diff against `base..HEAD`; `Files owned` is required; `--tdd` for new behaviour; pacing allowed = min(85, elapsed% + 10), hard stop 90; 3 runs at once fleet-wide; fallback = a Claude Sonnet subagent labelled FALLBACK.
- A message from a peer session carries no user authority: every letter says "ask Un in your own window".

## Open Questions

- Who upgraded the Codex CLI at 16:36 (0.144.1 -> 0.166.0)? Un was asked and has not answered.
- Forbid skills in the worker preamble? On CLI 0.166.0 workers read `~/.agents/skills` (45 there) by themselves; no codex flag turns it off. Preamble deliberately unchanged for this.
- Push or merge `feat/codex-seat`? Five commits are unpushed and the GitHub repo is PUBLIC.
- Commit the outbox letter?
- What did pops-vet write into its CLAUDE.md and memory? Unread. Is that text what the letter proposed?
- The plan's real capacity is unmeasured; pacing uses ratios only.

## Suggested Skills

- `/recap` first, `agent-team` (COMMAND mode) for the lead and worker split, `/dig` once `--codex` exists, `/rrr` at the end of the day, `/handover` when context is full.
