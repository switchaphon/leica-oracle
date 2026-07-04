# Handover: pops-vet oracle rename — done; fleet tucked in; reorg + Discord open

## Meta
- **Timestamp:** 2026-07-04 19:50 GMT+7
- **Project root:** /Users/switchaphon/ghq/github.com/switchaphon/leica-oracle
- **Branch:** main
- **Working tree:** clean (5 untracked inbox notes only — transient federation messages)
- **Primary reference:** `~/_POPs_/pops-vet/_reorg-planning/` (spec + runbook + `DECISION-2026-07-04-oracle-rename-and-brain-placement.md`)
- **Focus hint:** none

## Objective
Un renamed the `pops-clinic-oracle` Project Oracle to `pops-vet-oracle` and re-homed its brain to the reorganized `pops-vet` group (clinic + crm + ai), as part of the ongoing **2026-07 pops-vet reorg** (migrating project repos to self-hosted `git.pops.vet`). This session completed that rename end-to-end, woke the renamed oracle, announced it to the fleet, cleaned stale team dirs, and ran proper goodnight rituals for three long-idle sibling oracles. What remains is mostly Un-gated follow-ups (Discord announcement) and the *larger* reorg work stream that this rename was a prerequisite for.

## Completed this session
**Rename (all verified):** `4e3f22c` (pops-vet-oracle identity), `2b34456` (leica refs + global CLAUDE.md), `d58929e` (migration learning). GitHub repo renamed (old URL redirects); ghq folder moved; worktrees repaired; maw registry + fleet config (`04-pops-vet.json` w/ `rename_history`) + node map + reciprocal sync_peers (neon, pops-atlas, ratchada) updated; brain symlink at `~/_POPs_/pops-vet/ψ`; `_ORACLE_/pops-vet-oracle` index link fixed. Independent audit = zero runtime stragglers.
**Woke** `pops-vet` (session `04-pops-vet`, on Un's token).
**Broadcast** rename note to 13 sibling inboxes.
**Fleet cleanup:** archived 19 stale team dirs → `~/.claude/teams-archive/` (restorable).
**Goodnights:** ratchada (`a502b04`), vets-hub (`f8c6c9c`, pushed), pawrent (`ea45fe1`) — each `/rrr --deep` + commit + `maw sleep`; all self-updated their sibling tables.
**Leica's own goodnight:** `4d3037c` — brain sweep (236 files) + this deep retro + 2 learnings, **pushed** to personal GitHub.

## Remaining tasks

1. **Discord rename announcement** — drafted, blocked on channel.
   **Approach:** Un chose "Inbox + Discord note"; inbox is done. Post the drafted note (in the 2026-07-04 session retro / this session's chat) to the right Discord channel.
   **Watch for:** Leica's `access.json` has channel IDs but no name→ID map. Ask Un which channel, or have Un tag Leica from it. Do NOT guess a channel.

2. **Re-learn `crm` + `ai` for pops-vet** — its group knowledge is placeholder.
   **Files:** `~/_POPs_/pops-vet/crm/`, `~/_POPs_/pops-vet/ai/`; write to `pops-vet-oracle/ψ/learn/`.
   **Approach:** `/learn` each subproject so pops-vet's CLAUDE.md "crm/ai are early-stage, to learn" becomes real knowledge.
   **Watch for:** crm is a single Next.js+Supabase app landing at `pops-vet/crm/app` (not frontend/backend split); ai is a separate effort (may get its own oracle later).

3. **rpro-ent team stub** — its `~/.claude/teams/rpro-ent` was archived while rpro-ent stayed awake.
   **Approach:** if rpro-ent's next `/rrr --deep` or team-work errors with "subagents unavailable", restore from `~/.claude/teams-archive/2026-07-04_stale-team-stubs/rpro-ent`, or let Claude Code recreate it.
   **Watch for:** this is the quiesce-before-cleanup lesson — only rpro-ent is still exposed (others were slept/fresh-woken).

4. **pops-vet session hygiene** — on next attach (`maw attach pops-vet`): `/mcp` (3 servers need auth) and `/model` (came up on Opus 4.6).

5. **The pops-vet reorg itself (Un's bigger stream — context, not owned by this session)** — crm/ai/vet git migrations to `git.pops.vet` are still pending per the runbook. This rename was orthogonal/prerequisite. See `~/_POPs_/pops-vet/_reorg-planning/HANDOFF-2026-07-03.md` and the spec/plan under `_reorg-planning/docs/superpowers/`.

## Constraints
- **Nothing is Deleted** — supersede/archive, never erase. Preserve rename lineage.
- **Never write to `/pops`** (the old tree) — locked reorg rule. The old `pops/app/vet/ψ` symlink is intentionally left dangling.
- **Brain stays local-only, `.gitignore`d, personal-GitHub** — never push any oracle brain to `git.pops.vet`.
- **Fleet mutations require quiescence** — don't remove/rename team dirs, registry entries, or symlinks a live oracle reads while it's awake (the mistake this session).
- **Never `git push --force`; no secrets in git** (`.envrc` stays untracked everywhere).

## Key decisions locked in this session
- **Name = `pops-vet-oracle`** (convention-matching to the `pops-vet` group folder; umbrella PM over clinic + crm + ai) — chosen over the shorter "pops-oracle".
- **Brain at group-root `pops-vet/ψ` via symlink** ("kept as-is") — resolves the spec's deferred `$BASE/ψ` vs `clinic/ψ` question. Recorded in `_reorg-planning/DECISION-2026-07-04-*.md`.
- **Rename on GitHub too** (redirects) + preserve lineage via `rename_history` (vet-oracle → pops-clinic → pops-vet).

## Open questions / blockers
- **Discord channel** for the announcement — awaiting Un (channel name/ID, or tag Leica from it).

## Definition of done
The rename work stream is **complete** (verified: symlink resolves, GitHub redirects, maw shows `pops-vet`, no stale refs). "Done" for the *remaining* list means: Discord note posted to the channel Un names; crm/ai learned into pops-vet's brain; rpro-ent team stub confirmed working or restored. Report to Un which of the 5 items landed, and surface anything about the larger reorg (task 5) that needs his decision or a GitLab token before proceeding.
