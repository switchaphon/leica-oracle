# Oracle 101 — Ch08: Workflow UseCase

**Source**: https://oracle101.vercel.app/ch08.html
**Learned**: 2026-05-08

---

## 13-Step SDLC Pipeline

1. Receive request
2. Triage (REQ/CR/BUG classification)
3. GitHub issue creation (if long-term tracing needed)
4. Discord forum post with tags
5. Task Brief creation (scope + acceptance criteria)
6. Dev delegation via `maw hey`
7. Developer executes `maw workon repo slug`
8. Feature branch development + testing
9. PR creation via `maw pr`
10. QA routing (direct to Kati/QA agent)
11. PASS/FAIL iteration loop
12. Merge per project policy
13. `maw done` + Discord status update + handoff doc

---

## Communication Protocol

### Heartbeat Pattern
```bash
maw hey gale "[leaf] PROGRESS: finished API route"     # Every 5 min
maw hey gale "[bamboo] STUCK: build fails at ..."       # Immediate
maw hey gale "[kati] DONE: QA PASS PR #N"               # On completion
```

### Silence Escalation
| Duration | Action |
|----------|--------|
| 5 min | Expected progress update |
| 10+ min | Lead checks via `maw capture` |
| 20+ min | Escalation or restart |

---

## Discord as SDLC Surface

Discord is NOT casual chat — it's the official tracking surface.

### Forum Tags
| Tag | Usage |
|-----|-------|
| REQ | New requirements/user stories |
| CR | Change requests |
| BUG | Bug reports / QA failures |
| DEV | Active development |
| QA | Verification results |
| DEPLOY | Ready or completed |
| DONE | Loop closure |

---

## Worktree-First Workflow

```bash
maw workon <repo> <slug>
# Work + commit + verify with evidence (tests, screenshots, curl)
maw pr
maw hey kati "QA: PR #<N> on <repo>. Check: <acceptance>"
maw hey gale "[leaf|bamboo] DONE: PR #<N> — sent to Kati."
# After merge, from HOME BASE (not worktree!):
maw done <window-name>
```

**Critical**: `maw done` must run from home base, not from inside worktree (avoids self-targeting deadlock).

---

## Pre-Work Checklist (5 questions)

1. Issue type? (requirement / CR / bug / QA / deploy / doc)
2. Which project? (assign to correct PM/dev)
3. Source of truth location?
4. Required deliverables? (PR / QA / docs / deploy)
5. Definition of done?

---

## Worktree Policy Tiers

| Tier | Scope | Policy |
|------|-------|--------|
| **Strict** | Production repos | Hook-enforced mandatory `maw workon` |
| **Preferred** | General software | Warns against direct push, permits with caution |
| **Unrestricted** | Oracle tooling, low-risk | Contextual usage |

---

## QA Feedback Loop

```
FAIL → routes back to SAME branch/PR/worktree
     → dev fixes in same branch
     → pushes to existing PR
     → QA retests
     → prevents PR multiplication
     → after 3 consecutive failures → escalate to lead
```

---

## Safety Hooks (arra-safety-hooks)

Non-bypassable protections:
- Block `rm -rf` with broad paths
- Block `git reset --hard`, force push
- Block direct main branch pushes (strict repos)
- Block cross-boundary PR/comment creation

> When hooks block: change the process, not the hook. Never `--no-verify`.

---

## Handoff & Closure

Every completed task needs:
- Discord post/tag updates
- PR links
- QA PASS/FAIL documentation
- `maw done` execution
- Retrospective notes

> "Workflow ที่ดีทำให้ agent ไม่ใช่แค่ตอบคำถาม แต่เป็นระบบงานที่อ่านต่อได้ ตรวจซ้ำได้ และส่งต่อได้"
> (Good workflow transforms agents from responders into auditable, verifiable, transferable systems.)
