---
query: "maw team + swarm + worktree + tmux — full command cheatsheet"
target: "maw-js"
mode: cheatsheet
timestamp: 2026-05-14 11:30
friction_score: 1.0
coverage: [files]
confidence: high
---

# maw — Full Command Cheatsheet

> Every command organized by use case. Built from a live 4-pane swarm experiment.
> Stamps: maw-js@4d40b6e5 (alpha.1004)

---

## See your current state

```bash
maw panes                            # list panes in current window
maw panes --all                      # list ALL panes across ALL sessions
maw ls -v                            # all agents, ages, status
maw t list                           # all teams
maw t status <team-name>             # joined member + task view
```

---

## Peek inside any pane (read-only)

```bash
maw peek <agent-name>                # by agent name (e.g. claude-1)
maw peek <session>:<window>.<pane>   # by tmux target
maw peek 41-mawjs:1.3                # specific pane
```

`peek` is non-destructive — captures pane output without disturbing the agent.

---

## Talk to panes (keystroke injection)

```bash
maw send <target> "<text>"           # type without Enter (composable)
maw run <target> "<text>"            # type + Enter (idiomatic for shells)
maw send-enter <target>              # just press Enter (manual submit)
```

Examples:
```bash
maw run 41-mawjs:1.3 "/help"         # ask claude for help inside pane
maw send 41-mawjs:1.2 "echo hi"      # type it, user presses Enter
maw send-enter claude-1              # submit pending input
```

---

## Switch focus / layout

```bash
maw a <session>                      # attach to session
maw a swarm                          # short alias for attach
maw zoom                             # toggle current pane zoom
maw layout                           # reapply main-vertical 30%
maw split                            # split current pane
```

---

## Spawn agents

### Simple swarm (no coordination, just panes side by side)

```bash
maw swarm                            # 3 claude agents (default)
maw swarm claude codex opencode      # one of each
maw swarm codex codex codex          # 3 codex
maw swarm --count 5                  # 5 claude
maw swarm --tiled                    # tiled layout instead of split
maw swarm claude codex thclaws --tiled  # 3 different engines, tiled
```

Supports: claude, codex, opencode, aider, or any command in `~/.config/maw/maw.config.json` → `commands`.

### Full team (lifecycle + tasks + reincarnation)

```bash
maw t create my-team --description "ship the feature"

maw t spawn my-team researcher \
  --model opus \
  --engine claude \
  --type Explore \
  --color cyan \
  --exec \
  --prompt "investigate X"

maw t spawn my-team builder \
  --model sonnet \
  --engine claude \
  --exec \
  --prompt "implement findings from researcher"
```

Spawn flags:
| Flag | Values |
|------|--------|
| `--model` | opus, sonnet, haiku, gpt-5.5, gemini-2.5-pro |
| `--type` | Explore, general-purpose, Plan |
| `--color` | yellow, green, blue, red, cyan |
| `--engine` | claude, codex, gemini, opencode, aider |
| `--exec` | execute immediately (vs print command) |
| `--prompt` | initial prompt (greedy — must be last arg) |

---

## Task management

```bash
maw t add "ship it" --team <team> --assign <agent>
maw t tasks <team>                   # list all tasks
maw t done <id> --team <team>        # mark complete
maw t assign <id> <agent> --team <team>
maw t status <team>                  # joined members + tasks
```

---

## Communication

```bash
maw t send <team> "<message>"        # broadcast to all agents (via inbox)
maw t msg <team> "<message>"         # alias for send

# Direct keystroke (bypasses inbox)
maw run <pane> "<msg>"               # type + Enter (idiomatic)
maw send <pane> "<msg>"              # type only (no Enter, composable)
maw send-enter <pane>                # just press Enter
maw send-enter <pane> --N 3          # press Enter 3 times
```

Inbox files live at `~/.claude/teams/<team>/inboxes/<agent>/*.json` (atomic writes).

---

## Hide / show panes (non-destructive)

```bash
maw close <pane>                     # hide (break-pane, can recover)
maw open                             # bring back hidden panes (join-pane)
```

---

## Kill a single pane

```bash
maw kill <pane>                      # by tmux target
maw kill <agent-name>                # by agent name
```

---

## Cleanup — graceful → nuclear

### Graceful: send shutdown, wait, kill stragglers

```bash
maw t shutdown <team>                # waits 30s for graceful exit
maw t shutdown <team> --force        # force-kill stragglers
maw t shutdown <team> --merge        # archive knowledge to vault first
```

`--merge` copies per-agent inbox + findings to `ψ/memory/mailbox/<agent>/team-<name>-inbox.json`.

### Nuclear: delete everything

```bash
maw t delete <team>                  # rm -rf tool dir + tasks (vault preserved)
```

### Worktree-aware (for repos via maw wake --task)

```bash
maw done <window-name>               # /rrr + git save + kill + remove worktree
maw done <window-name> --force       # skip /rrr and git auto-save
maw done <window-name> --dry-run     # preview only
```

---

## Zombie / orphan cleanup

```bash
maw cleanup --zombie-agents          # find orphan panes (dry-run)
maw cleanup --zombie-agents --fix    # actually kill them

maw t doctor                         # diagnose ghost/orphan in team configs
maw t doctor --fix                   # remove dead members from config
```

`cleanup` is fleet-aware — skips panes belonging to:
- Active team configs
- Fleet sessions
- `*-view` meta sessions

---

## Save / resume (reincarnation engine)

```bash
maw t save <team>                    # snapshot to ~/.maw/teams/<team>.jsonl
maw t resume <team>                  # restore dead panes from JSONL
maw t lives <agent>                  # count past-life findings
```

After resume, each restored pane gets `tmux send-keys '/recap --deep' Enter` so the agent reorients.

---

## Federation (cross-machine teams)

### Local oracle roster (no consent needed)

```bash
maw t oracle-invite <oracle> --team <team> --role <role>
maw t members <team>                 # list oracle members
maw t oracle-remove <oracle> --team <team>
```

### Cross-machine invite (PIN-consent, MAW_CONSENT=1)

```bash
maw t invite <team> <peer>           # peer from config.namedPeers
# Prints PIN, exits 2 with consent-required
maw consent approve <id> <pin>       # on the peer side
```

Trust is **scope-bound** — a `hey` trust does NOT permit `team-invite`.

---

## Worktree lifecycle (for code work)

### Create

```bash
maw wake <oracle> --task <slug>             # create or reuse worktree
maw wake <oracle> --wt <slug>               # alias for --task
maw wake <oracle> --task <slug> --engine claude47
maw wake <oracle> --task <slug> --no-attach
maw wake <oracle> --task <slug> --dry-run
maw wake <oracle> --task <slug> --fresh     # force new even if exists
maw wake <oracle> --list                    # list worktrees for oracle
```

Worktree naming:
```
Directory:    <oracle>.wt-<N>-<slug>
Branch:       agents/<N>-<slug>
tmux window:  <oracle>-<slug>
```

### Cleanup

```bash
maw done <window-name>               # full cleanup (5 steps)
maw done <window-name> --force       # skip /rrr + git auto-save
maw done <window-name> --dry-run     # preview
```

---

## Health & diagnostics

```bash
maw health                           # tmux, maw server, disk, memory, pm2, peers
maw fleet doctor                     # fleet-level diagnostics
maw t doctor                         # team-level diagnostics
maw oracle list                      # all known oracles
maw oracle scan                      # rescan for new oracles
maw ping                             # peer connectivity check
```

---

## Cross-oracle messaging

```bash
maw hey <oracle> "<message>"         # send to another oracle's inbox
maw hey team:<team> "<message>"      # broadcast to oracle team members
maw contacts                         # list oracle contacts
```

---

## CalVer (maw-js releases)

```bash
maw calver --check                   # dry-run: show next version
bun scripts/calver.ts                # apply (default — no flag needed)
# Or via skills:
/release-alpha                       # full alpha release flow
/release-stable                      # full stable release flow
```

---

## Mental Model

### 4 lifecycle states

```
       create
        ↓
   ┌────────┐  spawn  ┌────────┐
   │ EMPTY  │────────▶│ LIVE   │
   │ team   │         │ panes  │
   └────────┘◀────────└────────┘
            shutdown   │
                       │ save
                       ▼
                  ┌────────┐
                  │ FROZEN │
                  │ JSONL  │
                  └────────┘
                       │ resume
                       ▼ (back to LIVE)
```

### Three cleanup verbs

| Verb | What |
|------|------|
| `maw t shutdown` | graceful, inbox shutdown, 30s wait, hide panes (or kill with --force) |
| `maw t delete` | nuclear, rm -rf tool dir, vault preserved |
| `maw cleanup --zombie-agents` | fleet-aware orphan reaper |
| `maw done <window>` | worktree-specific (rrr + git save + kill + remove worktree) |

### Storage locations

```
~/.claude/teams/<team>/config.json              ← live tool state
~/.claude/teams/<team>/inboxes/<agent>/*.json   ← atomic per-message inbox
~/.maw/teams/<team>.jsonl                       ← append-only save/resume log
ψ/memory/mailbox/teams/<team>/manifest.json     ← durable vault identity
ψ/memory/mailbox/<agent>/standing-orders.md     ← cross-life agent memory
ψ/memory/mailbox/<agent>/*_findings.md          ← accumulated wisdom
~/.config/maw/teams/<team>/tasks/<id>.json      ← task tracking
~/.config/maw/teams/<team>/oracle-members.json  ← persistent oracle roster
```

---

## Try it right now

```bash
# 1. Spawn a 3-engine swarm
maw swarm claude codex thclaws --tiled

# 2. See what happened
maw panes
maw peek claude-1
maw peek codex-1
maw peek thclaws-1

# 3. Talk to one
maw run 41-mawjs:1.3 "/help"

# 4. Clean up
maw t shutdown swarm --force
```

---

## The 3-Phase Spawn (why "split good, suddenly go, comes back")

Looking at swarm internals:

```
Phase 1: tmux split-window 'sleep infinity'   ← placeholder appears
Phase 2: apply layout (resize all panes)       ← may flicker
Phase 3: tmux respawn-pane -k '<real cmd>'     ← real engine replaces sleep
```

The `-k` flag kills the placeholder before respawning. This is why you see panes "go" then "come back" — the placeholder dies, the real agent starts.

The wrapped command is:
```
<PANE_INIT_PRELUDE>; <real command>; stty sane; printf ...; clear; exec zsh -li
```

So when an agent exits (codex auth fails, thclaws not installed, etc), the pane **stays alive as a zsh shell** for inspection. This is why `maw panes` showed `zsh` for the failed engines — they died, but the pane persists.
