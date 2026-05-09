# Oracle 101 — Ch06 + Ch06B: Maw Commands (Core → Standard → Extra)

**Source**: https://oracle101.vercel.app/ch06.html + ch06b.html
**Learned**: 2026-05-08

---

## Command Tiers

| Tier | Count | When |
|------|-------|------|
| Core 12 | Foundation | Every oracle needs these |
| Standard 25 | Common ops | Typical team setups |
| Extra 30 | Specialized | Federation, teams, advanced |

---

## Core 12 Commands

| Command | Purpose |
|---------|---------|
| `maw init` | First-run wizard — config, session, paths |
| `maw ls` | List all visible sessions and windows |
| `maw oracle ls` | Fleet status (awake, sleeping, missing) |
| `maw wake` | Open/attach oracle session. Flags: `--task`, `--issue`, `--pr`, `--fresh` |
| `maw sleep` | Reduce activity, keep knowledge |
| `maw stop` | Halt entire fleet |
| `maw health` | Validate system (tmux, server, resources) |
| `maw ping` | Quick peer/node connectivity check |
| `maw peek` | Screenshot pane visuals |
| `maw take` | Move windows between sessions |
| `maw bud` | Create new Oracle from existing (yeast budding) |
| `maw done` | Close lifecycle — retro + cleanup |

---

## Standard 25 Commands

### Events & Triggers
```bash
maw on <oracle> <event>          # Session-level triggers
maw on <oracle> <event> --once   # Fire once
maw on <oracle> <event> --timeout 30m
```

### Identity & Diagnostics
| Command | Purpose |
|---------|---------|
| `maw whoami` | Current operational context |
| `maw session` | Session metadata |
| `maw about <oracle>` | Oracle details |

### Monitoring & Navigation
| Command | Purpose |
|---------|---------|
| `maw overview` | War room dashboard |
| `maw panes` | List panes with metadata |
| `maw zoom` | Toggle tmux focus |
| `maw capture <name> --lines N` | Retrieve text from panes (for automation) |

**capture vs peek**: Capture returns text. Peek shows visual screenshot.

### Fleet & Plugin Management
```bash
maw fleet ls / health / doctor   # Fleet operations
maw plugin init / build / install  # Plugin lifecycle
```

### Federation & Communication
```bash
maw transport status             # Cross-node messaging diagnostics
maw federation status            # Multi-node state
```

### Memory Sync
```bash
maw soul-sync                    # Sync ψ/memory between Oracles
```

---

## Extra 30 Commands (Advanced)

### Team & Multi-Agent

| Command | Purpose |
|---------|---------|
| `maw mega` | MegaAgent teams for large projects |
| `maw team create / spawn / send` | Temporary agent squads — dissolves after task |
| `maw avengers` | Multi-role team composition |

### Federation & Messaging

| Command | Purpose |
|---------|---------|
| `maw pair` / `maw peers` | Peer management |
| `maw reunion` | Trigger federation sync |
| `maw broadcast "msg"` | Fleet-wide messaging |
| `maw talk-to <name> "msg"` | Persistent threaded conversations (1:1) |

### Context Management

| Command | Purpose |
|---------|---------|
| `maw park <agent>` | Suspend without killing context |
| `maw resume <agent>` | Restore parked agent |
| `maw workon <repo> <slug>` | Create worktree + tmux window |
| `maw workspace` | Multi-node workspace management |

### Cleanup & Diagnostics

| Command | Purpose |
|---------|---------|
| `maw cleanup --zombie-agents` | Kill orphaned panes |
| `maw doctor` | Diagnostic checks with auto-healing |
| `maw signals` | Monitor bud/absorb signals |

---

## Key Patterns

| Pattern | When to use |
|---------|-------------|
| `talk-to` vs `broadcast` | 1:1 conversation vs fleet-wide announcement |
| `park` / `resume` | Pause work preserving context, continue later |
| `capture` vs `peek` | Text for automation vs visual for humans |
| `maw on` vs persistent triggers | Session-scoped vs fleet-wide config |

## Selection Framework

Start Core → escalate to Standard for tmux/fleet → Extra for federation/teams.
Stub commands = entry points only (scaffolding for future).
