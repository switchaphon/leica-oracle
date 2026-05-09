---
source: "maw-js source code + oracle101.vercel.app + docs/comparison/team-agents-vs-maw-team.md"
date: 2026-05-08
tags: [architecture, sessions, tmux, team-agents, fleet, routing, oracle-design]
confidence: verified (confirmed from source code)
---

# Oracle Session Architecture — The Definitive Pattern

## The Rule

**แต่ละ Oracle อยู่ session ของตัวเอง ห้าม join-pane ข้าม session.**

```
Session: 04-neon              Session: 05-pops-clinic
├── Pane 0: neon-oracle       ├── Pane 0: pops-clinic-oracle
│   (MAIN — maw hey routes    │   (MAIN — maw hey routes
│    here always)              │    here always)
├── Pane 1: researcher@neon   ├── Pane 1: chrome@pops-clinic
│   (team-agent, temporary)   │   (team-agent, temporary)
└── Pane 2: reviewer@neon     └── (killed after task done)
    (killed after task done)
```

## Why (from source code evidence)

### 1. `resolveOraclePane` (comm-send.ts:14-29)
```
"when an oracle window has multiple panes (e.g., team-agents split beside it),
tmux's send-keys defaults to the LAST-ACTIVE pane — which becomes whichever
teammate just spawned, not the oracle itself."

"Strategy: pick the lowest-index pane running an agent. Pane 0 is conventionally
the oracle's main pane (created by maw wake); team-agents spawn LATER as splits
and take higher indexes."
```
**Meaning**: Pane 0 = Oracle. Higher panes = team-agents. maw hey always routes to Pane 0.

### 2. `spawnTeammatePane` (layout-manager.ts:119-150)
```
tmux split-window -t '<leader-pane>' -h -P -F '#{pane_id}' '<command>'
```
**Meaning**: Team-agents split from the Oracle's pane WITHIN the same session. They are children of the Oracle, not siblings.

### 3. `cmdTeamShutdown` (team-lifecycle.ts:50-127)
```
- Send shutdown via structured inbox to each teammate
- Wait up to 30s for panes to die
- Force-kill stragglers if --force
- cleanupTeamPanes: hide or kill leftover panes
- cleanupTeamDir: remove config
```
**Meaning**: When task is done, team-agent panes are killed. Oracle survives alone.

### 4. `resolveFleetSession` (wake-resolve-impl.ts:245-253)
```
Reads fleet/*.json → matches windows[].name → returns config.name (session name)
```
**Meaning**: Fleet config is the source of truth for routing. If session name doesn't match fleet config, routing breaks.

## The Two Layers of Teams

### Layer 1: team-agents (within Oracle's session)
- **Spawned by**: `maw team spawn <team> <role> --exec`
- **Lives in**: Split pane within Oracle's tmux window
- **Purpose**: Execute a specific task (code, review, research)
- **Lifecycle**: spawn → work → report DONE → shutdown → kill pane
- **Routing**: Not directly addressable by `maw hey` — only the Oracle (Pane 0) receives messages
- **Example**: Chrome spawns a `tester` and `implementer` for a feature

### Layer 2: Oracle fleet (each in own session)
- **Spawned by**: `maw wake <oracle>` or `maw bud <name>`
- **Lives in**: Own tmux session (e.g., `04-neon`, `05-pops-clinic`)
- **Purpose**: Persistent identity, project ownership, cross-session memory
- **Lifecycle**: wake → work → sleep/done → wake again next session
- **Routing**: Directly addressable by `maw hey <oracle-name> "message"`
- **Example**: neon-oracle, pops-clinic-oracle, nodered-simulator-oracle

### The killer differentiator (from docs/comparison)
> "maw team oracle-invite brings federation oracles into a team.
> team-agents cannot do this — it operates inside a single Claude Code session.
> That's the dividing line: in-session vs cross-oracle."

## The Complete Flow

```
1. Un tells Leica: "have pops-clinic review the lab modal"
2. Leica sends: maw hey pops-clinic "review lab modal, brief Chrome"
3. maw resolves: pops-clinic → fleet config → session 05-pops-clinic → Pane 0
4. pops-clinic receives message, decides to delegate
5. pops-clinic spawns: maw team spawn pops-clinic chrome --exec
6. tmux splits: Pane 1 (chrome@pops-clinic) appears beside Pane 0
7. chrome@pops-clinic works on the task
8. chrome reports DONE via team inbox
9. pops-clinic runs: maw team shutdown pops-clinic
10. Pane 1 killed. Only Pane 0 (pops-clinic-oracle) survives.
11. pops-clinic reports: maw hey leica "DONE: lab modal reviewed"
```

## What NOT to Do

| Wrong | Why | Right |
|-------|-----|-------|
| `tmux join-pane` Oracle into Leica's session | Removes Oracle from its session → fleet routing breaks | Use `maw peek` or `maw a <session>` to observe |
| `tmux send-keys` directly | No pane resolution, no idle check, no auto-wake | Use `maw hey <oracle> "message"` |
| Split pane for another Oracle | Creates confusion about which session owns the pane | Each Oracle = own session, team-agents = splits within |
| Kill an Oracle's session to "clean up" | Destroys the Oracle's tmux presence | Use `maw sleep` or `maw done` |

## Observation Methods (for the human or lead Oracle)

| Method | Use case |
|--------|----------|
| `maw peek <oracle>` | Quick look at what the Oracle is doing (text capture) |
| `maw a <session>` | Attach to the Oracle's session (full screen, interactive) |
| `maw panes` | List all panes across all sessions with metadata |
| `maw overview` | War room dashboard |
| `maw capture <oracle> --lines N` | Get text output for automation |

## Fleet Config Must Match Session Name

The session name created by `maw wake` includes a numeric prefix (e.g., `04-neon`).
The fleet config `~/.config/maw/fleet/<oracle>.json` field `name` must match exactly.

```json
// ~/.config/maw/fleet/neon.json
{
  "name": "04-neon",    // ← MUST match tmux session name
  "windows": [{ "name": "neon-oracle", "repo": "switchaphon/neon-oracle" }]
}
```

If mismatched → `resolveFleetSession` returns wrong name → `maw hey` can't find session → delivery fails.

**Fix applied 2026-05-08**: Updated 6 fleet configs where `name` was bare (e.g., "neon") but session was prefixed (e.g., "04-neon").

---

*Verified from maw-js v26.5.7 source code. This is how Nat designed it.*
