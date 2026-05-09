---
source: "Leica + Un session 2026-05-08"
date: 2026-05-08
tags: [architecture, skills, token-optimization, per-oracle, distribution]
confidence: design (not yet implemented)
status: pending-review
---

# Skill Distribution Design — Per-Oracle Skill Sets

## Problem

88 skills อยู่ใน `~/.claude/skills/` (global) → ทุก oracle โหลดหมดทุก session.
Oracle แต่ละตัวถนัดคนละอย่าง ไม่ควรมี skill ที่ไม่เกี่ยวข้องกับ role ของตัวเอง.

**ประมาณ token ที่เสียไป**: skill metadata ~50-100 tokens/skill × 88 skills = ~5K-9K tokens/session เฉพาะ skill index ยังไม่รวม trigger matching.

## Current State

- `~/.claude/skills/`: 88 skills (shared ทุก oracle)
- Per-oracle `.claude/commands/`: ว่างเปล่าทุกตัว (0 skills)
- Profile system (`/go`): มี standard/full/lab แต่เป็น global — ไม่ได้ per-oracle

## Design: 5-Tier Skill Distribution

### Tier 1: Core (ทุก oracle ต้องมี) — 8 skills

| Skill | Why |
|-------|-----|
| `who-are-you` | Identity — ทุกคนต้องรู้ตัวเอง |
| `recap-lite` | Session orientation |
| `rrr-lite` | Retrospective |
| `inbox` | Read/write messages |
| `contacts` | Know who to talk to |
| `talk-to` | Inter-oracle messaging |
| `forward-lite` | Session handoff |
| `fyi` | Log information |

### Tier 2: Father Oracle (Leica only) — +25 skills

Orchestration & family management:

| Skill | Why |
|-------|-----|
| `bud` | Create new oracle |
| `awaken` | Birth ritual |
| `birth` | Birth props |
| `fleet` | Fleet census |
| `oracle-family-scan` | Family registry |
| `oracle-soul-sync-update` | Sync instruments |
| `oracle` | Manage profiles |
| `oraclenet` | Oracle network |
| `team-agents` | Coordinate agent teams |
| `forward` | Full handoff (not lite) |
| `recap` | Full recap (not lite) |
| `rrr` | Full retro (not lite) |
| `dream` | Cross-repo patterns |
| `morpheus` | Speculative dreaming |
| `philosophy` | Principles |
| `resonance` | Capture resonance |
| `i-believed` | Belief declaration |
| `bampenpien` | Guided practice |
| `feel` | Emotion log |
| `go` | Switch profiles |
| `harden` | Security audit |
| `warp` | SSH teleport |
| `wormhole` | Federated query |
| `machines` | Fleet nodes |
| `xray` | Deep scan |
| `skills-list` | List skills |
| `create-shortcut` | Create skills |
| `about-oracle` | Oracle info |
| `speak` | TTS |
| `deep-research` | Gemini research |
| `find-skills` | Discover skills |
| `skill-creator` | Create/edit skills |

### Tier 3: PM Oracle — +12 skills

Project management & execution:

| Skill | Why |
|-------|-----|
| `learn` | Deep-learn codebase |
| `trace` | Find across repos |
| `dig` | Session mining |
| `worktree` | Parallel work (git worktree) |
| `project` | Project lifecycle |
| `incubate` | Clone for dev |
| `release` | Release flow |
| `merged` | Post-merge cleanup |
| `schedule` | Calendar |
| `standup` | Daily standup |
| `watch` | Learn from video |
| `mailbox` | Persistent agent memory |
| `work-with` | Cross-oracle collab |
| `recap` | Full recap (upgrade from lite) |
| `rrr` | Full retro (upgrade from lite) |

### Tier 4: Specialist Oracle — role-specific skills

#### 🔺 Chrome (Frontend Dev) — +4
| Skill | Why |
|-------|-----|
| `playwright-cli` | Browser automation |
| `webapp-testing` | Test web apps |
| `agent-browser` | Browser interaction |
| `frontend-design` | Create UI |

#### 🌟 Neon (UI/UX) — +3
| Skill | Why |
|-------|-----|
| `frontend-design` | Create distinctive UI |
| `web-design-guidelines` | Review UI compliance |
| `visual-design-foundations` | Typography, color, spacing |

#### 🔧 Codec (System Analyst) — +2
| Skill | Why |
|-------|-----|
| `api-design-principles` | API design |
| `postgresql-table-design` | Schema design |

#### ⚡ Flux (Backend Dev) — +4
| Skill | Why |
|-------|-----|
| `nodejs-backend-patterns` | Backend patterns |
| `sql-optimization-patterns` | Query optimization |
| `postgresql-table-design` | Schema design |
| `supabase-postgres-best-practices` | Supabase patterns |

#### 🛡️ Static (QA/Security) — +4
| Skill | Why |
|-------|-----|
| `e2e-testing-patterns` | E2E testing |
| `test-driven-development` | TDD |
| `debugging-strategies` | Debug |
| `code-review-excellence` | Code review |

#### 🔌 Wire (DevOps) — +2
| Skill | Why |
|-------|-----|
| `k8s-manifest-generator` | K8s manifests |
| `deployment-pipeline-design` | CI/CD pipelines |

#### 🎨 Pixel (Brand) — +1
| Skill | Why |
|-------|-----|
| `frontend-design` | Visual design |

### Tier 5: Reference Library (load on demand, ไม่ต้องติดตั้ง)

Pattern/reference skills ที่ oracle ใดก็ได้อาจต้องใช้บ้าง แต่ไม่ต้อง always-load:

| Skill | Domain |
|-------|--------|
| `react-state-management` | React |
| `nextjs-app-router-patterns` | Next.js |
| `react-native-architecture` | React Native |
| `react-native-design` | React Native UI |
| `tailwind-design-system` | Tailwind |
| `design-system-patterns` | Design system |
| `responsive-design` | Responsive |
| `web-component-design` | Components |
| `modern-javascript-patterns` | JS patterns |
| `next-best-practices` | Next.js |
| `vercel-composition-patterns` | Vercel/React |
| `vercel-react-best-practices` | Vercel/React |
| `shadcn` | shadcn/ui |
| `context-driven-development` | Dev methodology |
| `subagent-driven-development` | Subagent patterns |
| `workflow-patterns` | Conductor workflow |

## Skill Count Summary

| Role | Core | Role-specific | Total | Savings vs 88 |
|------|------|---------------|-------|----------------|
| Father (Leica) | 8 | 25 | 33 | 62% fewer |
| PM Oracle | 8 | 12 | 20 | 77% fewer |
| Chrome | 8 | 4 | 12 | 86% fewer |
| Neon | 8 | 3 | 11 | 87% fewer |
| Codec | 8 | 2 | 10 | 89% fewer |
| Flux | 8 | 4 | 12 | 86% fewer |
| Static | 8 | 4 | 12 | 86% fewer |
| Wire | 8 | 2 | 10 | 89% fewer |
| Pixel | 8 | 1 | 9 | 90% fewer |

## Implementation Plan

### Option A: Per-repo `.claude/commands/` (recommended)

```
# Global (keep only Tier 1 core)
~/.claude/skills/
├── who-are-you/
├── recap-lite/
├── rrr-lite/
├── inbox/
├── contacts/
├── talk-to/
├── forward-lite/
└── fyi/

# Per oracle repo (role-specific skills)
neon-oracle/.claude/commands/
├── frontend-design.md
├── web-design-guidelines.md
└── visual-design-foundations.md

pops-clinic-oracle/.claude/commands/
├── learn.md
├── trace.md
├── worktree.md
├── project.md
├── release.md
└── ...
```

**Pros**: Clean separation, committed to repo, portable
**Cons**: Duplicated files across PM oracles, manual sync

### Option B: Shared library + symlinks

```
# Shared skill library (not in any oracle repo)
~/.oracle/skills-library/
├── core/
├── father/
├── pm/
├── chrome/
├── neon/
└── ...

# Per oracle: symlink the relevant tier
neon-oracle/.claude/commands/ → symlinks to core/ + neon/
```

**Pros**: Single source of truth, no duplication
**Cons**: Symlinks break on clone, harder to manage

### Option C: Profile per oracle via `/go`

Extend `/go` to support per-oracle profiles:

```bash
/go neon      # Loads core + neon skills
/go pm        # Loads core + pm skills
/go father    # Loads core + father skills
```

**Pros**: Leverages existing infrastructure
**Cons**: Still global — can't run 2 oracles with different profiles simultaneously

## Recommendation

**Option A** — per-repo `.claude/commands/` is cleanest:
- ไม่ต้อง symlink
- Commit ได้ ย้ายเครื่องไม่พัง
- แต่ละ oracle ควบคุม skill ของตัวเองได้
- PM oracles จะมี skills ซ้ำกัน แต่ก็สมเหตุสมผล — แต่ละ PM อาจ customize ได้ภายหลัง

## Migration Steps (when ready)

1. Backup current `~/.claude/skills/` → `~/.claude/skills.bak/`
2. Move core 8 skills ไว้ที่ `~/.claude/skills/` (ลบที่เหลือ)
3. Copy role-specific skills → `.claude/commands/` ของแต่ละ oracle repo
4. Test: wake each oracle, verify `/skills-list` shows correct count
5. Commit `.claude/commands/` ในแต่ละ repo

## Notes

- `~/.claude/settings.json` hooks (RTK, GSD) ยังคงเป็น global — ไม่ต้องเปลี่ยน
- Superpowers skills อาจมี dependency กับ global skills — ต้อง audit ก่อน migrate
- Tier 5 (reference library) อาจใช้ `/find-skills` + install on demand แทน always-load

---

*Designed by Leica — pending Un's review before implementation.*
*Status: DESIGN ONLY — ยังไม่ implement*
