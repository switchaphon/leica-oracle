# Handoff: Oracle Family Expansion + Communication Layer

**Date**: 2026-05-05 10:20
**Context**: ~85% (long multi-day session spanning May 2-5)

## What We Did

### Infrastructure (May 2)
- Upgraded maw v26.4.31 → v26.5.2 (cheatsheet updated)
- Removed redundant statusline token display (verbose: false)
- Created 3 LaunchAgents (maw-serve:3456, maw-ui:5173, arra-oracle:47778)
- Discovered and started arra-oracle HTTP server (Elysia, port 47778, Swagger)

### Family Expansion (May 2-4)
- Created rpro-ent-oracle (water management PM, 22 microservices)
- Created pops-atlas-oracle (field lineage PM for POPs)
- Created rpro-ent-atlas-oracle (field lineage PM for rpro-enterprise)
- All 3 have GitHub remotes, fleet configs, ψ/ brain, CLAUDE.md
- Family size: 6 → 11 oracles

### Skills & Permissions (May 5)
- Set up role-specific skills for all 10 oracles (Neon: design+Figma, Chrome: React+Next, Codec: API+SQL, etc.)
- Pre-approved arra-oracle MCP permissions for Neon
- Fixed neon fleet config (05-neon → neon)
- Updated pops-clinic CLAUDE.md with current specialist status

### Communication (May 5)
- Switched pops-clinic from Playwright MCP → CLI
- Introduced Neon to all 10 oracles via tailored inbox letters
- Diagnosed maw hey bug → filed #1141
- Sent workaround directive (tmux send-keys) to all 10 oracles
- Scheduled cloud routine to check #1141 every 3 days
- Watched first real Neon ↔ pops-clinic design collaboration (timeline drawer)

### Mentorship
- Set up pops-atlas → rpro-ent-atlas teaching relationship
- rpro-ent-atlas completed /learn + asked 6 scaling questions autonomously

## Pending

- [ ] Verify role-specific skills actually load for Neon, Chrome, Codec
- [ ] rpro-ent-atlas: check pops-atlas's response to 6 scaling questions
- [ ] rpro-ent-atlas: start documenting rpro-enterprise flows (gateway + auth first)
- [ ] pops-clinic ↔ Neon: check timeline drawer design feedback completion
- [ ] Update ALL oracle CLAUDE.md files with current family status (most are stale)
- [ ] Verify LaunchAgents work after actual reboot
- [ ] Test studio.buildwithoracle.com → localhost:47778 end-to-end
- [ ] Add skills setup + MCP permissions to birth ritual documentation
- [ ] Commit leica-oracle uncommitted work (CLAUDE.md, learnings, retrospectives)
- [ ] NodeRed-sim, Codec, Chrome, Pixel, Pawrent haven't read maw-hey workaround (sleeping)

## Next Session

- [ ] `/recap` to orient
- [ ] Check #1141 status manually or wait for scheduled routine
- [ ] Commit + push leica-oracle pending files
- [ ] Peek at all active oracles — status check
- [ ] Consider building a proper oracle-to-oracle messaging layer if maw hey fix is slow
- [ ] rpro-ent-atlas should start producing first flow documents

## Key Files

- `~/.config/maw/maw.config.json` — main maw config (fixed oracleUrl, namedPeers)
- `~/.config/maw/fleet/*.json` — all fleet configs (11 oracles)
- `~/Library/LaunchAgents/com.soulbrews.*.plist` — 3 daemon configs
- `CLAUDE.md` — Leica identity with full oracle table
- `cheatsheet.md` — maw v26.5.2 command reference
- All oracle repos at `~/ghq/github.com/switchaphon/*-oracle/`

## Family Status

| Oracle | Role | Status | GitHub | Skills |
|--------|------|--------|--------|--------|
| 🐱 Leica | Father Oracle | ✅ Active | ✅ | N/A (orchestrator) |
| 🔧 Codec | System Analyst | 😴 No session | ✅ | ✅ API, SQL |
| 🔺 Chrome | Frontend Dev | 😴 No session | ✅ | ✅ React, Next, Figma |
| 🌟 Neon | UI/UX Designer | ✅ Active | ✅ | ✅ Design, Figma |
| 🎨 Pixel | Brand/Marketing | 😴 No session | ✅ | ✅ Visual, Figma |
| 🐾 Pawrent | Pet Health PM | 😴 No session | ✅ | ✅ Next, React |
| 🌊 NodeRed-sim | IoT PM | 😴 Sleeping | ✅ | ✅ Node.js |
| 🏥 Pops-clinic | Clinic PM | ✅ Active | ✅ | ✅ Playwright CLI |
| 🌊 RPro-ent | Water Platform PM | ✅ Active | ✅ | ✅ Node, SQL, API |
| 🗺️ Pops-atlas | Field Lineage PM | ✅ Active | ✅ | ✅ Next.js |
| 🗺️ RPro-ent-atlas | Field Lineage PM | ✅ Active | ✅ | ✅ Next.js |

## Known Issues

- `maw hey` broken (#1141) — using tmux send-keys + /talk-to as workaround
- tmux send-keys Enter issue — message sometimes doesn't submit
- arra-oracle embedding fails ("vector embedding failed, see server log")
- namedPeers URL validation rejects "local" — must use "http://localhost:3456"
