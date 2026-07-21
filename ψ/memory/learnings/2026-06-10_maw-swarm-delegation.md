# Lesson: Follow delegation model — maw swarm codex for dev, lead reviews

**Date**: 2026-06-10
**Context**: User asked pops-clinic-oracle (lead) to spawn Codex (developer) via `maw swarm codex` on a tmux pane. Lead coded everything directly instead. User corrected. Codex was then used for review and found 3 real bugs.

## Key Takeaways

1. **Respect the workflow instruction** — "spawn Codex to implement" means spawn Codex, not do it yourself. The process tests multi-agent orchestration, not just code output.

2. **maw swarm codex pattern**:
   - `maw swarm codex` → spawns Codex pane in current tmux window
   - `maw send-text "05-pops-clinic:add-service-fee-prototype.2" '<brief>'` → send task
   - `maw peek "05-pops-clinic:add-service-fee-prototype.2"` → check progress
   - `tmux capture-pane -t "..." -p -S -500` → capture full scrollback
   - `maw kill "..."` → close pane when done

3. **Codex review is cheap and effective** — GPT-5.5 read 5 files + PRD in 2 minutes, found: fabricated IDs, price inconsistency, duplicate key bug. Cost ~$0.30.

4. **Wait for Next.js full compile** before Playwright navigation:
   ```bash
   until grep -q "compiled" /tmp/pops-dev.log; do sleep 2; done
   ```
   Not just `curl` status code — a 200 can still serve broken chunks.

## Tags
`maw`, `swarm`, `codex`, `delegation`, `multi-agent`, `playwright`, `next-dev`
