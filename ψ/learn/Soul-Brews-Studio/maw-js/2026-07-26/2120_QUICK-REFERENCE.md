# maw-js Quick Reference — v26.6.14-alpha.2110

> Multi-Agent Workflow in Bun/TS. Remote tmux orchestra control.  
> **Repo**: Soul-Brews-Studio/maw-js | **Channel**: alpha | **Language**: TypeScript/Bun

---

## Table of Contents
1. [Installation](#installation)
2. [Global Command Structure](#global-command-structure)
3. [Core Commands (Built-in Routes)](#core-commands-built-in-routes)
4. [Top-Level Aliases](#top-level-aliases)
5. [Plugin Commands](#plugin-commands)
6. [Configuration](#configuration)
7. [State Directories](#state-directories)
8. [Environment Variables](#environment-variables)
9. [Key Features & Workflows](#key-features--workflows)

---

## Installation

### From npm/bun
```bash
bun add -g maw-js
# or
npm install -g maw-js@latest
```

### From Source (Development)
```bash
cd maw-js
bun install
bun build src/cli.ts --outfile dist/maw --target=bun --minify
./dist/maw --version
```

### Bin Entry
```json
{
  "bin": {
    "maw": "./src/cli.ts"
  }
}
```

---

## Global Command Structure

### Dispatch Order (Priority)
1. **Verbosity flags** (`--quiet`, `-q`, `--silent`, `-s`) — stripped early
2. **Core routes** (hey, send, notify, peek, etc.) — from `route-comm`
3. **Tool routes** (plugins, plugin, artifacts, agents, audit, tmux, serve) — from `route-tools`
4. **Top-level aliases** (wake, attach, team, etc.) — from `top-aliases.ts`
5. **Plugin registry** (beta) — user + bundled plugins
6. **Agent shorthand** (`maw <agent> <message>`) — last resort

### Version & Update
```bash
maw --version                    # Show version
maw -v                          # Same as above
maw version                     # Same as above
maw update                      # Update maw-js
maw upgrade                     # Alias for update
```

---

## Core Commands (Built-in Routes)

### Communication (route-comm)

#### `maw hey <target> <message> [flags]`
**Pane-inject message with signed identity envelope**
- Target forms: `<oracle-window>` | `local:<agent>` | `<session>:<window>[.<pane>]` | `<node>:<session>[:<window>]`
- Flags:
  - `--from <node:oracle>` — explicit sender (env fallback: `MAW_SENDER`)
  - `--inbox` — queue to inbox only; skip pane injection
  - `--approve` — bypass cross-scope ACL queue
  - `--trust` — persist sender↔target trust entry
  - `--no-verify-submit` — skip post-send probe (~800ms faster, use in tight loops)
  - `--force` — deprecated (delivery forced by default)
- Example:
  ```bash
  maw hey mawjs-oracle "task complete"
  maw hey local:mawjs "hello"
  maw hey phaith:01-hojo:3 "cross-node msg"
  ```

#### `maw send <target> <message> [flags]`
**Alias of `maw hey`** (identical behavior; both pane-inject with signed envelope + trailing Enter)
- See `maw hey` for all flags
- Note: For raw text (no envelope, no Enter), use `maw send-text`

#### `maw notify <target> <message> [flags]`
**Routine push to recipient's ψ/inbox/** (does NOT pane-inject)
- Same flags as `maw hey`, except:
  - `--force` is ignored (delivery always inbox-only)
  - `--inbox` is implicit
- Pairs with:
  - `maw hey` (urgent, pane-injecting)
  - `maw broadcast` (fleet-wide)
- Recipients pull via `maw inbox --unread`

#### `maw peek [node:]<agent>`
**Federation-aware pane reader** (cross-node capable)
- Read tmux pane output
- Supports full federation targeting
- Example: `maw peek phaith:mawjs`

---

### Plugin Management (route-tools)

#### `maw plugins [ls|info|remove|lean|standard|full|nuke|enable|disable] [flags]`
**List and manage installed plugins**
- Subcommands:
  - `ls` (default) — list installed plugins
  - `info <name>` — show plugin details
  - `remove <name>` — uninstall plugin
  - `lean` — show only essentials
  - `standard` — show standard tier plugins
  - `full` — show all + disabled
  - `nuke` — remove all (destructive)
  - `enable <name...>` — enable disabled plugins
  - `disable <name>` — disable plugin
- Flags: `--json`, `--all`, `-v/--verbose`, `--core`, `--standard`, `--extra`, `--api`, `--force`

#### `maw plugin [init|build|install|create|ls|info|remove|enable|disable] [args]`
**Plugin lifecycle management**
- `init` — initialize a new plugin
- `build` — compile plugin
- `dev` — development mode
- `install --standard` — bootstrap standard plugins from binary
- `create [--rust | --as] <name> [--here]` — scaffold new plugin
- `ls` — list (compact by default; `-v` for full table)
- `info <name>` — plugin metadata
- `remove/uninstall <name>` — uninstall
- `enable <name...>` / `disable <name>` — toggle state
- Filters: `--core`, `--standard`, `--extra`, `--api`

#### `maw artifacts [ls|get] [team] [task-id] [flags]`
**Query Claude task artifacts**
- `ls` — list artifacts
- `get [team] [task-id]` — fetch specific artifact
- Flags: `--json`

#### `maw agents [--json] [--all] [--node <node>]`
**List active agents**
- Shorthand: `maw agent`
- Flags: `--json`, `--all`, `--node <node>`

#### `maw audit [limit]`
**Show audit log** (command usage history)
- Optional: `limit` — number of entries

#### `maw tmux <verb> [args]`
**Low-level tmux control verbs**
- Verbs: `peek`, `ls`, `attach`, `kill`, `open`, `close`, `zoom`, `pipe`, `sync`
- Flags:
  - `--json`, `--all`, `--compact`, `--verbose`, `--roster`, `--fleet-only`
  - `--recent` / `-r` — sort by recency
  - `--readonly` / `--read-only` — read-only mode
  - `--input` / `--output` / `--no-output` — pipe control
  - `--only-if-closed` / `-o` — conditional
  - `--force` — bypass checks
  - `-s/--session` — target session
- See `maw tmux --help` for full documentation

#### `maw serve [port] [--gateway bun|rust] [--as <name>] [--force-takeover] [--quiet|-q] [--verbose|-v...]`
**Start maw web server** (default: localhost:3456)
- Subcommands:
  - `status` / `--status` — show server status
  - `stop` — stop server
- Flags:
  - `--gateway [bun|rust]` — choose backend (default: bun)
  - `--as <name>` — named instance (multi-instance support)
  - `--force-takeover` — force if PID lock exists
  - `--quiet` / `-q` — suppress output
  - `-v` / `-vv` / `-vvv` — verbosity levels
- Env: `MAW_SERVE_VERBOSITY` (quiet|normal|verbose|debug|frames)

---

## Top-Level Aliases

These are short verbs that rewrite args or dispatch directly (defined in `top-aliases.ts`):

| Alias | Canonical | Description |
|-------|-----------|-------------|
| `a` | `attach` | Attach to tmux session; `--shell` for repo shell pane |
| `b` | `bring` | Thin alias for `wake --split` |
| `bring` | (direct) | Bring oracle HERE (split into current session) |
| `awake` | (direct) | Launch oracle process + engine (no /awaken) |
| `work` | (direct) | Alias: `wake --work .` (derive from cwd) |
| `wake` | (direct) | Wake/reuse oracle session (fuzzy + auto-clone) |
| `new` | (direct) | Create plain tmux workspace session |
| `ls` | (direct) | List local sessions; `--federation` for peers |
| `layout` | (direct) | Apply tmux layout preset (even-horizontal, main-vertical, etc.) |
| `t` | `team` | Team — create, spawn, send, shutdown |
| `kill` | `tmux kill` | Kill tmux pane/session |
| `split` | `split` | Split pane and attach |
| `open` | `tmux open` | Bring back hidden panes (join-pane) |
| `close` | `tmux close` | Hide panes without killing (break-pane) |
| `zoom` | `tmux zoom` | Toggle zoom on pane |
| `panes` | `tmux ls --all --verbose` | List all panes across sessions |
| `tile` | `tile` | Tile current window or spawn N panes |
| `scaffold` | `bud --scaffold-only` | Create oracle repo skeleton only |
| `preflight` | (direct) | Pre-flight check (version, plugins, agents, config) |
| `snapshots` | `fleet snapshots` | List/inspect recovery snapshots |
| `wtf` | (direct) | Read-only team drift doctor |
| `promote` | (direct) | Promote agent (advanced) |

### Wake/Awake Flags (All Comprehensive)
```bash
maw wake <oracle> [options]

Session Selection:
  --work             Override mode detection; work mode uses repo identity
  --oracle           Override mode detection; oracle mode  
  --session <name>   Target foreign workspace session instead of oracle's own
  --fresh/--new      Force new numbered worktree (default: reuse stable slot)
  --layout nested|legacy  Worktree filesystem layout

Worktree & Access:
  --pick             Open reusable worktree picker
  --name <name>      Create/reuse named stable worktree
  --wt <name>        Shorthand for --name
  --list             Preview worktrees only (no session/window creation)

Task & Flags:
  --task <slug>      Assign task via ψ/.lineage.yaml
  --wt <name>        Write worktree assignment
  --bud              With --task/--wt, write ψ/.lineage.yaml (no fleet mutation)
  --signal-on-birth  With --bud, drop parent birth signal
  --prompt <text>    Custom prompt
  --incubate <slug>  Incubate mode

Snapshots & Recovery:
  --from-snapshot    Restore missing windows from latest snapshot
  --snapshot <id>    Select specific snapshot

Rehydration:
  --main/--solo/--no-rehydrate  Skip rehydration (legacy)

Fleet & Nodes:
  --no-fleet         Skip fleet registration
  --all-local        Affect all local sessions

Execution:
  --attach           Attach after wake
  -a                 Shorthand: --attach
  --dry-run          Preview without executing
  --wait             Wait for engine after bootstrap (default: return immediately)
  -e/--engine <name> Choose execution engine (default: config.engines.default)

Parent/Session IDs (Advanced):
  --parent-session-id <id>  Set MAW_PARENT_SESSION_ID
  --session-id <id>         Set MAW_SESSION_ID

Examples:
  maw wake mawjs-oracle                          # Wake with defaults
  maw wake phaith:mawjs-oracle --engine claude  # Cross-node with specific engine
  maw wake . --work --pick                       # Derive from cwd, pick worktree
  maw wake myoracle --task my-feature --bud     # With task assignment
  maw awake myoracle -e codex                    # Launch without /awaken
```

---

## Plugin Commands

### Fleet Management

#### `maw fleet <subcommand> [args]`
**Manage persistent fleet registry** (use `maw ls` for live sessions)

| Subcommand | Purpose |
|------------|---------|
| `init` | Initialize fleet config |
| `ls` | List registered fleet |
| `rename <old> <new>` | Rename oracle session |
| `renumber <session> <num>` | Renumber session ID |
| `validate` | Check fleet consistency |
| `health` | Health diagnostics |
| `doctor [--reboot]` | Full doctor check; `--reboot` for auto-wake readiness |
| `config-doctor` | Check repo-local .claude/ drift |
| `consolidate` | Merge fleet state |
| `sync` | Synchronize with peers |
| `sync-windows` | Sync tmux windows across fleet |
| `snapshots` | List recovery snapshots |
| `restore` | Restore from snapshot |
| `snapshot <id>` | Inspect snapshot details |

### Tmux Session/Pane Control

#### `maw session` or `maw whoami`
**Print current tmux session name**

#### `maw attach <session> [--shell]`
**Attach to tmux session** (shorthand: `maw a`)
- `--shell` — attach in repo shell pane

#### `maw split [args]`
**Split pane and attach to session**

#### `maw open` / `maw close`
**Show/hide panes** (join-pane / break-pane)

#### `maw zoom <pane>`
**Toggle zoom on pane**

#### `maw pane swap <a> <b>`
**Swap panes in current window**

#### `maw panes`
**List all panes across sessions** (verbose detail)

#### `maw tile [N] [--wt <name>] [--path <dir>] [--cmd <cmd>]`
**Arrange window into grid or spawn N panes**
- `N` — number of panes (default: 2)
- `--wt <name>` — worktree name
- `--path <dir>` — directory for panes
- `--cmd <cmd>` — command to run in panes
- See `maw panes` to inspect; `maw pane swap` to move

#### `maw layout [<preset>]` or `maw layout <target> <preset>`
**Apply tmux layout preset** (shorthand: `maw layout`)
- Presets: `even-horizontal`, `even-vertical`, `main-horizontal`, `main-vertical`, `tiled`
- Alias: `reset` → `main-vertical`
- With explicit target: `maw tmux layout <target> <preset>`

### Team (Agent Reincarnation Engine)

#### `maw team <subcommand> [args]`
**Agent management across teams** (shorthand: `maw t`)

| Subcommand | Usage |
|-----------|-------|
| `create <name> [--description <text>]` | Create new team |
| `list` or `ls` (default) | List all teams; `--all` includes archived |
| `spawn <team> <role> [options]` | Spawn agent in team |
| `send <team> <agent> <message>` | Send msg to team agent |
| `msg` | Alias for `send` |
| `resume <name> [--model <model>]` | Resume dormant agent |
| `lives <agent>` | Show agent reincarnation history |
| `history <agent>` | Alias for `lives` |
| `shutdown <name> [--force] [--merge]` | Shut down team |
| `down <name>` | Alias for `shutdown` |
| `prune` | Cleanup orphaned state |
| `up <team> [options]` | Awaken entire team |
| `add <subject> [--team <name>] [--assign <agent>] [--description <text>]` | Add task to team |
| `tasks [team-name] [--team <name>]` | List team tasks |

**Team Spawn Flags:**
- `--engine <name>` or `-e <name>` — AI engine (claude, codex, etc.)
- `--model <model>` — model override
- `--cwd <path>` / `--worktree <path>` — execution directory
- `--prompt <text>` — custom system prompt
- `--exec` — execute immediately
- `--parent-session-id <id>` / `--parent <id>` — set MAW_PARENT_SESSION_ID
- `--session-id <id>` — set MAW_SESSION_ID

**Team Up Flags:**
- `--dry-run` — preview without execution
- `--status` — show status only
- `--force` — bypass checks
- `--gather` — gather team state
- `-e <engine>` — specific engine
- `--members <roles>` — comma-separated roles to spawn

### Configuration & Discovery

#### `maw config <subcommand> [flags]`
**Inspect cwd-aware config layers**
- `show` — show merged config
- `sources` — show config provenance
- `explain <key>` — explain specific key
- Flags: `--json`

#### `maw discover [--peers config|scout|both] [flags]`
**List federation peers, inventory sources, live tmux state**
- Flags:
  - `--peers [config|scout|both]` — peer source
  - `--json` — JSON output
  - `--tree` — tree view
  - `--awake` — show only awake nodes

#### `maw federation|fed <subcommand> [host] [flags]`
**Multi-node federation status, sync, expansion**

| Subcommand | Purpose |
|-----------|---------|
| `status` | Show federation state |
| `sync` | Synchronize fleet across nodes |
| `expand` | Plan federation expansion |

**Flags:**
- `--dry-run` — preview
- `--check` — validate
- `--prune` — cleanup orphaned
- `--force` — force action
- `--verify` — deep verification
- `--json` — JSON output
- `--probe` — network probe
- `--peers [config|scout|both]` — peer source
- `--port <port>` — override SSH port
- `--user <user>` — SSH user
- `--oracle <name>` — target oracle
- `--apply` — apply changes

#### `maw transport|tp [status]`
**Transport layer status and diagnostics**

### Oracle Management

#### `maw oracle|oracles [ls|scan|fleet|about|search] [flags]`
**Oracle management**
- `ls` — list oracles
- `scan` — discover oracles
- `fleet` — show fleet membership
- `about <name>` — details for oracle
- `search <query>` — search oracles
- Flags: `--json`, `--awake`, `--org <name>`, `--path`, `--stale`, `--sort-by born`

### Miscellaneous

#### `maw cli <oracle|session[:window]> [--json]`
**Print Claude CLI invocations** (ready-to-paste context)

#### `maw channel <add|rm|ls|providers|setup|test> [oracle] [plugin] [flags]`
**Manage Claude Code channels per oracle**
- Flags: `--env`, `--pass`, `--dev`, `--json`, `--verbose`, `--repo`, `--guild`, `--no-interactive`, `--dry-run`, `--remove-global`, `--to-repo`

#### `maw swarm [agents...] [--tiled] [--count N]`
**Spawn multi-AI agent panes** (side-by-side)
- Default agents: claude, codex, opencode
- `--tiled` — arrange in grid
- `--count N` — spawn N of each

#### `maw scheduler <start|stop|status|list|run> [--name <job>] [--json] [--dry-run]`
**File-based job scheduler** (dispatch `maw hey` on timer)
- `start` — start scheduler daemon
- `stop` — stop daemon
- `status` — show status
- `list` — list registered jobs
- `run` — run job immediately

---

## Configuration

### Config Files
- **System root**: `~/.claude/` or `MAW_HOME` (if set)
- **Global config**: `~/.maw/config.json` (or `$XDG_CONFIG_HOME/maw/config.json` with `MAW_XDG=1`)
- **Local config**: `.claude/maw.yml` or `.claude/maw.json` (per-repo overrides)
- **Team config**: `~/.claude/teams/<name>/config.json`
- **Fleet registry**: `~/.maw/fleet.json` (persistent session state)

### Config Keys (Common)
- `engines` — AI engine registry (claude, codex, etc.)
- `disabledPlugins` — disabled plugin names (array)
- `maxAgents` — concurrent agent cap
- `transport` — transport layer config (ssh, tmux, http)
- `federation` — peer nodes and routing
- `commands` — custom command definitions

### Plugin Discovery
- **Bundled**: `~/.maw/plugins/` (auto-symlinked by `runBootstrap`)
- **User**: `~/.oracle/commands/` (custom CLI commands in .ts/.js/.wasm)
- **Environment**: Symlinks or git checkouts in plugins dir

---

## State Directories

### XDG Compliance
- **Legacy** (default): `~/.maw/` + `~/.oracle/`
- **Modern** (with `MAW_XDG=1`):
  - Data: `~XDG_DATA_HOME/maw/` (plugins, fleet, snapshots)
  - Config: `$XDG_CONFIG_HOME/maw/` (config.json, teams)
  - Cache: `$XDG_CACHE_HOME/maw/` (temp work)

### Key Paths
| Path | Purpose |
|------|---------|
| `~/.maw/plugins/` | Installed plugins |
| `~/.maw/fleet.json` | Persistent fleet registry |
| `~/.maw/config.json` | Global maw config |
| `~/.oracle/commands/` | User-defined CLI commands |
| `~/.claude/teams/` | Team configurations |
| `~/.discord-state/` | Discord bot state (if enabled) |
| `.claude/maw.yml` | Per-repo config overrides |
| `ψ/inbox/` | Oracle inbox (messages) |
| `ψ/.lineage.yaml` | Worktree task metadata |

---

## Environment Variables

### Execution Context
| Variable | Purpose | Example |
|----------|---------|---------|
| `MAW_HOME` | Override `~/.maw/` root | `/alt/path/to/maw` |
| `MAW_XDG` | Enable XDG compliance | `1` |
| `MAW_PLUGINS_DIR` | Override plugin search dir | `/custom/plugins` |
| `MAW_CLI` | Set by cli.ts (internal) | `1` |
| `DISCORD_BOT_TOKEN` | Discord relay bot auth | (token) |
| `DISCORD_STATE_DIR` | Discord state dir override | `~/.discord-state/` |

### Session & Transport
| Variable | Purpose |
|----------|---------|
| `MAW_TEAM` | Explicit team context (override detection) |
| `MAW_SENDER` | Fallback sender identity for `--from` |
| `MAW_PARENT_SESSION_ID` | Parent session for spawned agents |
| `MAW_SESSION_ID` | Explicit session ID for this process |
| `MAW_ALLOW_SELF_BRING` | Allow split-bring into own pane |
| `TMUX` | Set by tmux when inside session |

### Performance & Tuning
| Variable | Purpose |
|----------|---------|
| `MAW_TEST_MODE` | Testing mode (disables real work) |
| `MAW_QUIET` | Suppress output |
| `MAW_SERVE_VERBOSITY` | Server verbosity (quiet|normal|verbose|debug|frames) |
| `MAW_NO_SCOUT` | Skip scout during serve startup |

---

## Key Features & Workflows

### Multi-Node Federation
- **Cross-node targeting**: `maw hey node:session:window <msg>` → SSH relay
- **Peer discovery**: `maw discover --peers config|scout|both`
- **Fleet sync**: `maw fleet sync` → consolidate state across nodes
- **Fallback**: If target node unreachable, auto-queue to inbox

### Team (Agent Reincarnation)
- **Create**: `maw team create myteam`
- **Spawn**: `maw team spawn myteam claude -e claude`
- **Persist**: Agents survive restarts via `team.json` state
- **Task tracking**: `maw team add "feature request" --assign claude`

### Worktree & Lineage
- **Auto-derive**: `maw work` ≡ `maw wake . --work` (from cwd)
- **Nested layout**: `repo/agents/N-X/` (N=instance, X=slot)
- **Legacy layout**: `.wt-N-X` (if `--layout legacy`)
- **Metadata**: `ψ/.lineage.yaml` tracks task assignment

### Recovery & Snapshots
- **Auto-snapshot**: Fleet auto-snapshots state before cleanup
- **Restore**: `maw fleet restore` or `maw wake --from-snapshot`
- `--snapshot <id>` — select specific snapshot
- **Healing**: `maw fleet doctor --reboot` for auto-wake readiness

### Inbox & Message Routing
- **Urgent (pane-inject)**: `maw hey <target> <msg>` → Enter into pane
- **Routine (queue)**: `maw notify <target> <msg>` → write to `ψ/inbox/`
- **Broadcast**: `maw broadcast <msg>` → fleet-wide push
- **Pull**: `maw inbox --unread` → fetch queued messages

### Plugin Lifecycle
- **Install**: `maw plugin install <name>` | `maw plugin install --standard`
- **Bootstrap**: `maw plugin install --standard` — pull official plugins
- **Dev mode**: `maw plugin dev <path>` — symlink for testing
- **Disable/Enable**: `maw plugin disable <name>` | `maw plugin enable <name>`

### Scheduling
- **Job scheduler**: `maw scheduler start` (daemon mode)
- **File-based**: Define jobs in config; auto-dispatch `maw hey` on timer
- **Status**: `maw scheduler status` + `maw scheduler list`

### Preflight & Diagnostics
- **Quick check**: `maw preflight` — version, plugins, agents, config
- **Fix mode**: `maw preflight --fix` — auto-heal common issues
- **Fleet health**: `maw fleet doctor` — comprehensive diagnostics
- **Team drift**: `maw wtf` — read-only team state check
- **Audit**: `maw audit [N]` — command usage history

### Web UI & Serve
- **Start**: `maw serve [port]` (default: 3456)
- **Multi-instance**: `maw serve 3456 --as primary` + `maw serve 3457 --as secondary`
- **Gateway choice**: `--gateway [bun|rust]` (default: bun)
- **Verbosity**: `-q` (quiet) | `-v` / `-vv` / `-vvv` (verbose)
- **Status**: `maw serve --status` | `maw serve stop`

---

## Flag Summary by Command

### Commonly Used Flags
| Flag | Applies To | Meaning |
|------|-----------|---------|
| `-h`, `--help` | Most | Show help (parsed early for core routes) |
| `--json` | ls, config, etc. | JSON output |
| `--dry-run` | federation, fleet, etc. | Preview without executing |
| `--force` | plugins, shutdown, etc. | Bypass safety checks |
| `--quiet` / `-q` | Global | Suppress normal output |
| `--verbose` / `-v` | Most | Detailed output |
| `--all` / `-a` | ls, teams, etc. | Include archived/hidden |
| `--node <name>` | federation, agents | Target specific node |

### Wake-Specific Flags
| Flag | Purpose |
|------|---------|
| `--work` / `--oracle` | Session mode selection |
| `--session <name>` | Foreign workspace target |
| `--fresh` | Force new worktree |
| `--pick` | Interactive worktree picker |
| `--name <name>` | Stable worktree name |
| `--task <slug>` | Assign task |
| `--bud` | Write ψ/.lineage.yaml only |
| `--attach` / `-a` | Attach after wake |
| `--wait` | Wait for engine |
| `-e` / `--engine <name>` | Execution engine |

---

## Examples & Patterns

### Common Workflows

#### Start a Team Session
```bash
maw team create myteam --description "Dev squad"
maw team spawn myteam claude -e claude
maw team spawn myteam code -e codex
maw team send myteam claude "investigate bug #123"
```

#### Wake an Oracle with Task
```bash
maw wake myoracle --task feature-x --bud --attach
# ψ/.lineage.yaml written; user attached to session
```

#### Cross-Node Message
```bash
# From node1, message agent on node2
maw hey node2:myoracle:0 "status check"

# Route via explicit sender
maw hey node2:agent --from node1:relay "hello"
```

#### List Federation State
```bash
maw discover --peers both --json
# Shows local + peer inventory

maw federation status --peers config
# Federation health check
```

#### Team Reincarnation
```bash
maw team resume claude --model claude-opus-4
# Resurrect claude agent with new model
```

#### Full Fleet Recovery
```bash
maw fleet snapshots
# List recovery snapshots

maw fleet restore <snapshot-id>
# Restore from snapshot

maw fleet doctor --reboot
# Ensure auto-wake on reboot
```

#### Worktree Inspection
```bash
maw wake myoracle --list
# Preview available worktrees without creating session

maw wake . --work --pick
# Derive oracle from cwd; interactive worktree picker
```

#### Tmux Tile & Pane Management
```bash
maw tile 4 --path ~/projects/myrepo
# Create 4-pane grid in current window

maw panes
# List all panes with metadata

maw pane swap 0 1
# Swap panes 0 and 1

maw layout main-vertical
# Resize to main-vertical layout
```

---

## Version Info

- **Current**: 26.6.14-alpha.2110
- **Branch**: alpha
- **Language**: TypeScript (Bun runtime)
- **License**: BUSL-1.1
- **Repository**: Soul-Brews-Studio/maw-js

Check version: `maw --version`  
Update: `maw update` or `maw upgrade`

---

## References

- **CLI Dispatch**: `src/cli/dispatch.ts` (command routing)
- **Command Registry**: `src/cli/command-registry.ts` (user + builtin plugins)
- **Usage**: `src/cli/usage.ts` (help formatting)
- **Top Aliases**: `src/cli/top-aliases.ts` (verb shortcuts)
- **Route Comm**: `src/cli/route-comm.ts` (hey, send, notify, peek)
- **Route Tools**: `src/cli/route-tools.ts` (plugins, artifacts, agents, tmux, serve)
- **Plugin System**: `src/plugin/registry.ts` + `src/plugin/manifest.ts`
- **Team Implementation**: `src/commands/plugins/team/impl.ts`
- **Fleet Management**: `src/commands/plugins/fleet/`
- **Package.json**: Exports + bin entry + scripts

---

**Last updated**: 2026-07-26  
**Generated from**: maw-js alpha.2110 source tree analysis  
**Scope**: Complete CLI surface documentation — every top-level command and major subcommand
