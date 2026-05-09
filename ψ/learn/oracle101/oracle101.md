# Oracle 101 Learning Index

## Source
- **URL**: https://oracle101.vercel.app/
- **Language**: Thai
- **Scope**: Complete Oracle system guide — foundation, runtime, teams, ops

## Explorations

### 2026-05-08 0940 (4 docs)
- [0940_SKILLS-MAW-PLUGIN](2026-05-08/0940_SKILLS-MAW-PLUGIN.md) — Three layers: memory, skills, maw, plugins. Profiles, installation order.
- [0940_MAW-COMMANDS](2026-05-08/0940_MAW-COMMANDS.md) — Core 12 → Standard 25 → Extra 30 commands. Federation, messaging, teams.
- [0940_ORCHESTRATION](2026-05-08/0940_ORCHESTRATION.md) — Three-tier delegation (Arrows/Squads/Federation), task briefs, heartbeat, failure modes.
- [0940_WORKFLOW-USECASE](2026-05-08/0940_WORKFLOW-USECASE.md) — 13-step SDLC pipeline, worktree-first, QA loop, safety hooks.

**Key insights**:
- Three layers must install in order: memory → skills → maw → plugins (never reverse)
- Three delegation tiers: Arrows (≤5min) → Squads (5-30min) → Federation (30min+) — always choose lowest
- Every delegation needs a reporting contract embedded in the initial prompt
- Discord is the SDLC surface, not casual chat — uses forum tags for tracking
- `maw done` must run from home base, never from inside worktree
