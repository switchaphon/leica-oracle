# Learning: Renaming a Project Oracle (in-place, non-destructive)

**Date**: 2026-07-04
**Context**: Renamed `pops-clinic-oracle` → `pops-vet-oracle` and re-pointed its brain access symlink to the new group root (`~/_POPs_/pops-vet/ψ`), during the 2026-07 pops-vet reorg. Un chose the convention-matching name (matches the `pops-vet` group folder) over the shorter "pops-oracle".

## The pattern: an Oracle rename touches 9 surfaces

A Project Oracle is a standalone ghq repo on **personal GitHub**, symlinked into the project. Renaming is **in-place** (preserves git history + brain), NOT a fresh bud. Surfaces, in order:

1. **GitHub remote** — `gh repo rename <new>` from inside the repo (renames on GitHub, auto-updates `origin`, old URL redirects).
2. **Local ghq folder** — `mv <old> <new>`.
3. **Git worktrees** — if the repo has worktrees (e.g. codex `agents/`), `mv` breaks their absolute gitdir pointers → `git worktree repair <newpath>...` with **explicit** new paths (bare `repair` only fixes the main tree; leftover worktrees show `prunable`).
4. **In-repo identity** — `start.sh` (hardcoded path), `README`, `CLAUDE.md` (name, scope, paths, Discord/federation strings, symlink doc, footer lineage). `.envrc` needs no change if it uses `$PWD`.
5. **maw registry** — `~/.config/maw/oracles.json` (repo/name/local_path; keep budded_from/at). Rename fleet config `NN-<name>.json` + update contents (name, window, project_path, sync_peers self-ref, `rename_history`). Rename team dir `~/.claude/teams/<name>`.
6. **maw federation-node map** — `~/.config/maw/maw.config.json` (+ `.50.json`) `agents` map: both `<name>` and `<name>-oracle` keys. (Stale entries here produce a phantom "uncertain / not cloned" row in `maw oracle list`.)
7. **Reciprocal sync_peers** — grep ALL fleet configs; other oracles list this one as `sync_peer`, and children list it as `budded_from`. Update those or federation refs dangle.
8. **Access symlink** — create new (`ln -s .../oracle/ψ <project>/ψ`); ensure `ψ` gitignored wherever it lands (n/a if the dir isn't a git repo).
9. **Parent + global** — leica `CLAUDE.md` Project-Oracles table, leica `start.sh`, global `~/.claude/CLAUDE.md` Project-PMs table.

## Gotchas

- **Quiesce first.** Live tmux session → `maw sleep` (graceful Claude exit), then `maw kill --force` the empty shell before `mv` (the fleet guard refuses a plain kill).
- **`mv` is safe on APFS** even with open FDs / gitstatus daemon (FDs track the inode); the live *shell* is the real concern, not the daemon.
- **Don't rewrite history.** ~50 historical retrospectives/learnings/inbox mention the old name — true when written (Principle 1). Only touch LIVE identity/config/forward-pointers. Preserve lineage: `renamed_from` + `rename_history` + footer chain (Vet Oracle → POPS Clinic Oracle → POPS Vet Oracle).
- **Brain placement was a *deferred* decision, not a conflict.** The reorg spec said "Leica confirms placement with the user" and showed both `$BASE/ψ` and `clinic/ψ` — so group-root vs subgroup was mine+Un's to decide.
- **Confidence discipline:** first plan was ~50% because pre-flight found a live session + an authoritative spec I hadn't read. Reading the user's own spec raised it to ~85% (the "conflict" was a deferred decision). Read the authoritative docs before executing on a mid-flight project.

See [[2026-05-01_maw-fleet-config-contract]], [[2026-05-08_pm-oracle-work-culture]].
