# Oracle 101 — Ch07: Orchestration

**Source**: https://oracle101.vercel.app/ch07.html
**Learned**: 2026-05-08

---

## Core Principle

> "Delegation that works requires: clear tasks, matched expertise, and results merged at decision points."

Oracle is a **family of specialized agents**, not a monolithic AI. Human retains final architecture review, risk decisions, and merge authority.

---

## Three-Tier Delegation Framework

### Tier 1 — Arrows (≤5 min)
- Fire-and-collect research tasks
- Single agent, narrow question
- Bounded reports (<400 words)
- Read-only operations
- Invisible but fast

### Tier 2 — Squads (5-30 min)
- Named roles + TaskList
- Worktree isolation per agent
- Shutdown protocol required
- Lead monitors, doesn't compete on code
- Lead assigns, merges, verifies

### Tier 3 — Federation (30+ min)
- Real tmux processes surviving session death
- Cross-machine communication
- Requires heartbeat reporting
- Reporting contract in initial prompt
- `maw capture` + lifecycle closure + cleanup

### Decision Tree

```
Does work survive beyond session?      → Tier 3
Requires multi-role coordination?      → Tier 2
Short read/transform/research?         → Tier 1
Otherwise:                             → Solo in current session
```

**Rule: Choose lowest tier sufficient.**

---

## Task Brief Template (MUST for every delegation)

Every delegation requires:
1. Agent name + tier selection
2. Working directory/repo
3. Clear objective
4. Inputs, constraints, steps
5. Deliverables + branch expectations
6. Verification criteria
7. **Reporting contract**
8. Closure procedure

### Reporting Contract (embed in EVERY agent spawn)

```
Every 5 min: maw hey <lead> "[name] PROGRESS: <summary>"
If blocked:  maw hey <lead> "[name] STUCK: <reason>"
When done:   maw hey <lead> "[name] DONE: <artifact>"
```

---

## Heartbeat Protocol

| Silence Duration | Action |
|-----------------|--------|
| Every 5 min | Agent sends progress update |
| 10+ min silence | Lead checks via `maw capture <window>` |
| 20+ min silence | Escalation or restart |
| Immediate | STUCK reports with evidence |

---

## Delegation Pattern

### Correct
```bash
# Gale sends dev a brief to open THEIR OWN worktree
maw hey leaf "First run: maw workon <repo> <slug> --prompt '<task>'. Then follow lifecycle."
```

### Wrong
```bash
# Gale opening worktrees ON BEHALF of developers — creates wrong ownership
maw workon <repo> <slug>   # ← Gale should NOT do this for others
```

After PR creation → dev sends QA the submission → reports back to lead.

---

## Critical Failure Modes

| Failure | Cause | Prevention |
|---------|-------|-----------|
| Silent Agent | 30+ min no update | Heartbeat every 5 min, STUCK contract |
| Merge Conflicts | Multiple agents edit same files | Module-level branch ownership |
| Orphaned Worktrees | Dead agents leave uncleaned branches | `maw done` + lifecycle closer |
| Prompt Loss | Instructions sent post-session | Embed full contract in initial prompt |
| Wrong Tier Choice | Mismatched complexity | Use decision tree, prefer lowest tier |

---

## Memory ≠ Coordination

| System | Role | Analogy |
|--------|------|---------|
| maw-js | Routing, capture, session control | Nervous system |
| arra-oracle-v3 | Learning, tracing, handoff | Brain |
| ψ/ vault | Learning artifacts, retro, inbox | Notebook |
| maw-ui | Human visibility | Display |

> "Without maw, the system remembers but cannot coordinate. Without memory, maw executes but forgets."
