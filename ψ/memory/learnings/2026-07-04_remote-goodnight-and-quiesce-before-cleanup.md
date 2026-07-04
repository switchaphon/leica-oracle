# Learning: Remote goodnight ritual + quiesce-before-cleanup

**Date**: 2026-07-04
**Context**: After renaming pops-clinic-oracle → pops-vet-oracle (see [[2026-07-04_oracle-rename-migration]]), I put 3 long-idle detached oracles (ratchada 12d, vets-hub 9d, pawrent 1d) to bed with the proper goodnight ritual, driven remotely from Leica.

## Pattern: drive a son's goodnight from the parent

The fleet goodnight protocol ([[2026-05-09_goodnight-rule-reinforced]]) is: `/rrr --deep` + commit + push, then sleep. To drive it for an idle son **without attaching**:

1. `maw hey <son> "goodnight: (1) /rrr --deep, (2) commit ALL work, (3) reply DONE — I'll sleep you"` — auto-mode picks it up.
2. **Verify delivery** with a quick `maw peek <son>` (maw hey can land without visibly submitting; peek confirms it's processing, not stuck at the prompt).
3. **Watch for the commit**, not the reply — background poll the son's git HEAD:
   ```bash
   start=$(git -C <repo> rev-parse HEAD)
   for i in $(seq 1 150); do sleep 10
     cur=$(git -C <repo> rev-parse HEAD)
     [ "$cur" != "$start" ] && { echo "COMMITTED $cur"; exit 0; }
   done; echo TIMEOUT; exit 1
   ```
   Run it with Bash `run_in_background` → single completion notification when the commit lands.
4. `maw sleep <son>` (it will likely force-kill an idle auto-mode session on `/exit` — **harmless because it committed first**; transcript stays resumable).

**Tailor the commit target per son.** ratchada/vets-hub worked in their own oracle repos (watch that repo). pawrent worked in the *app* repo but `/rrr` writes to its **brain** via the ψ symlink — so watch `pawrent-oracle` (brain), and tell it to leave app junk (`.envrc`, `coverage-tmp/`) untracked.

## The bug: watch the artifact, not a keyword you control

My first watcher grepped the pane for `READY-TO-SLEEP` — and matched **my own instruction** echoed in the son's pane. False positive. A git-HEAD change (or a file mtime) is a concrete artifact the son produces; it can't be spoofed by text I sent. **Observe the effect, never the words.**

## The mistake: quiesce before mutating shared fleet state

I archived empty team-stub dirs (`~/.claude/teams/<oracle>/`) during a fleet-cleanup **while several oracles were still awake**. When those oracles' `/rrr --deep` tried to spawn their agent swarm, they hit *"subagents unavailable (session team error)"* and fell back to sequential main-agent analysis. Graceful, non-fatal — but avoidable.

**Why:** the stubs *looked* inert (0 members, mtime weeks old), but a live session still depends on its team dir when it spawns sub-agents. "Inert on disk" ≠ "unused by a live process."

**Rule:** mutate shared fleet state (team dirs, registry, symlinks a live session reads) only when the dependents are **down** — or restore the dependency before triggering the action that needs it. Do fleet team-cleanup *after* the final round of sleeps, not between them.

**Why:** protects live sessions; keeps `/rrr --deep` swarms working; avoids log noise that reads like a real failure.

See [[2026-07-04_oracle-rename-migration]], [[2026-05-08_pm-oracle-work-culture]], [[2026-05-22_symlink-over-migration]].
