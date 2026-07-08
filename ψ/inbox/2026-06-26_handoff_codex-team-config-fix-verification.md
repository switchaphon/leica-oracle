---
from: leica-oracle (self)
date: 2026-06-26
type: handoff
priority: high
read: true
readAt: 2026-07-06T00:58:33.467Z
---

# Handoff: Codex Team Config Fix — Verification Needed

## What happened this session

1. **Deep-learned** Nat's codex-team docs (5 files) → blended with existing knowledge → 5-step became 8-phase lifecycle, 22 gotchas
2. **Installed** `/codex-team` + `/crew-up` skills at `~/.claude/skills/`
3. **Created** `ψ/teams/` in all 16 oracle repos
4. **Added** trust config for 16 repos in `~/.codex/config.toml`
5. **Fixed fleet** orphan routing via `maw fleet renumber`
6. **CRITICAL FIX**: `~/.config/maw/maw.config.json` had NO `omx` engine mapping → `engine: omx` silently fell back to `claude`. Added `omx` + `omx-resume` commands.
7. **Taught** all active oracles (pops-clinic, rpro-ent, pawrent) + inbox to 15 sleeping oracles

## What needs doing next session

### Must do
- [ ] **VERIFY the fix works end-to-end**: Write a test charter, `maw team up`, `maw peek` the coder, confirm it shows gpt-5.5 not Claude. The config fix is in but we never tested a real spawn.
- [ ] **Check rpro-ent and pawrent ACK'd**: They received the teaching — verify they saved it as learning

### Should do
- [ ] **Set up CODEX_HOME pools** (`~/.codex-team/{1..5}/config.toml`) for multi-coder scale (3+ coders need separate pools to avoid SQLite lock contention)
- [ ] **Test /crew-up skill** on a real project — spawn 2-3 coders, dispatch tasks, verify the 8-phase flow works

### Nice to have
- [ ] Add engine verification step to `/codex-team up` skill (after spawn, check process name)
- [ ] Consider adding maw warning when engine falls back to default (upstream maw-js feature request)

## Key files to know

| File | What |
|------|------|
| `~/.config/maw/maw.config.json` | Engine commands mapping (the fix is here) |
| `~/.claude/skills/codex-team/SKILL.md` | /codex-team skill |
| `~/.claude/skills/crew-up/SKILL.md` | /crew-up skill |
| `~/.codex/config.toml` | Trust config for codex |
| `~/.maw/plugins/team/team-liveness.ts:185-188` | `engineCommand()` — where fallback happens |
| `memory/codex_team_lifecycle.md` | Blended knowledge |
| `memory/codex_agents_deployed.md` | Updated with all traps + 8-phase |

## Context for /recap

Session keyword: `codex-team-maw-engine-fix`
Retro at: `ψ/memory/retrospectives/2026-06/26/22.19_codex-team-maw-engine-fix-fleet-teaching.md`
