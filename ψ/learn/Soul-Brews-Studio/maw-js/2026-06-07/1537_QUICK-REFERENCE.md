# maw-js — Quick Reference

**Status**: Reference v1.0  
**Last updated**: 2026-06-07  
**Version**: CalVer (e.g. v26.5.20-alpha.2203)  
**Runtime**: Bun 1.3+  
**License**: BUSL-1.1  
**Repo**: https://github.com/Soul-Brews-Studio/maw-js

## What is maw-js?

Multi-Agent Workflow (maw) is a **CLI for running multiple AI agents across machines**. You wake agents in tmux windows, send them messages, watch their screens, track costs — all from one terminal. One node or twenty; same commands.

- **Engine-agnostic**: drives Claude Code, Codex, Aider, OpenCode
- **Federated**: cross-machine communication via HMAC-SHA256 signed HTTP (port 3456)
- **Plugin OS**: 89+ plugins; core + vendored registry + user installs
- **Team-aware**: persistent multi-agent coordination via charters or ephemeral spawns
- **Channel-integrated**: Discord/Telegram bots via `--channels` flag
- **Usage-driven**: 3,000+ invocations tracked; data-driven plugin tiers

---

## Installation

### One-line install
```bash
curl -fsSL https://raw.githubusercontent.com/Soul-Brews-Studio/maw-js/main/install.sh | bash
```

### Via bun
```bash
bun add -g github:Soul-Brews-Studio/maw-js
```

### From source
```bash
ghq get Soul-Brews-Studio/maw-js && cd "$(ghq root)/github.com/Soul-Brews-Studio/maw-js" && bun install && bun link
```

### Recovery if `maw: command not found`
```bash
# Self-heal
bun add -g github:Soul-Brews-Studio/maw-js

# Or one-shot auto-restore
bunx -p github:Soul-Brews-Studio/maw-js maw doctor

# Shell hook for auto-recovery on every init
source scripts/maw-heal.sh  # add to .bashrc / .zshrc
```

**Versioning**: CalVer `v{yy}.{m}.{d}[-alpha.{HHMM}]` (e.g. `v26.5.17-alpha.752`)

---

## Quick Start

```bash
# Start the API + UI server
maw serve                                # :3456 by default

# Download & run the federation lens UI
maw ui install                           # latest release
maw ui                                   # → http://localhost:3456/federation_2d.html

# List recent sessions
maw ls --recent 5

# Wake an agent (auto-clones if needed)
maw wake neo --split                     # side-by-side with current pane

# Send a message (default: inject + Enter)
maw hey neo "what are you working on?"

# Read their screen
maw peek neo

# Graceful shutdown
maw done work:review                     # auto-save + cleanup worktree + session

# Create a new oracle
maw bud myname --from parent             # budded child
maw bud myname --root                    # root oracle (no parent)
```

---

## Core CLI Commands

### Session & Lifecycle

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw ls` | — | Compact session summary |
| `maw ls -v` / `-c` | — | Detailed / compact view |
| `maw ls --recent [n]` | — | Sort by creation time |
| `maw new <name>` | `n` | Create plain tmux workspace |
| `maw attach <name>` | `a` | Attach to session or wake from fleet |
| `maw wake <oracle> [task]` | — | Wake agent in tmux (auto-clones if needed) |
| `maw wake --dry-run` | — | Preview wake plan without side effects |
| `maw wake --list` | — | Show available agents |
| `maw wake --from-snapshot <id>` | — | Restore from previous wake state |
| `maw awake <oracle>` | — | Launch oracle process with engine (no ritual) |
| `maw sleep <oracle>` | — | Graceful process stop |
| `maw restart <target>` | — | Restart a session |
| `maw done <worktree>` | — | Finish worktree gracefully (cleanup + session) |
| `maw kill <target>` | — | Immediate kill |
| `maw cleanup` | — | Clean zombie panes + prune stale registry |

### Messaging & Communication

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw hey <target> "<msg>"` | — | Send message + pane inject + Enter (federation-aware) |
| `maw send <target> "<msg>"` | — | Alias of `hey` |
| `maw notify <target> "<msg>"` | — | Inbox-only push, no pane inject |
| `maw send-text <pane> "<txt>"` | — | Raw text into pane, no envelope, no Enter |
| `maw broadcast "<msg>"` | `shout` | Fleet-wide broadcast |
| `maw peek <target>` | — | Federation-aware pane read |
| `maw capture <pane>` | — | Pane scrollback dump (`--full` for everything) |
| `maw follow <pane>` | — | Live tail of pane output (`--since`, `--grep`, `--quit-on-idle`) |
| `maw activity <pane>` | — | Classify pane state (busy / idle / stuck) |
| `maw talk-to <oracle>` | — | Cross-oracle signed message via federation |

**Message format** (federation-aware):
```
[node:sender] message content here
```
Slash commands (`/skill`, `$cmd`) preserved as-is; already-signed messages pass through unchanged.

### Fleet & Identity

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw oracle` | — | Show oracle identity + fleet view |
| `maw oracle set-nickname <name> "<desc>"` | — | Set display name |
| `maw about <oracle>` | — | Show oracle metadata |
| `maw fleet ls` | — | Fleet config + slot inventory |
| `maw fleet health` | — | Fleet health checks |
| `maw fleet doctor` | — | Fleet diagnostics + fixer |
| `maw locate <oracle>` | — | Find oracle across federation |
| `maw bud <name>` | — | Create new oracle repo |
| `maw bud <name> --from <parent>` | — | Budded from parent |
| `maw bud <name> --root` | — | Root oracle (no parent) |
| `maw bud <name> --org <org>` | — | Target different GitHub org |
| `maw bud <name> --repo <org/project>` | — | Seed from existing project's ψ/ |
| `maw bud <name> --issue <n>` | — | Tie bud to GitHub issue |
| `maw bud <name> --fast` | — | Skip wake step |
| `maw bud <name> --note "why"` | — | Birth note → ψ/memory/learnings/ |
| `maw bud <name> --dry-run` | — | Plan without executing |

### Federation & Peers

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw federation` | `fed` | Multi-node sync status + control |
| `maw peers add <name> <url>` | — | Register peer by URL |
| `maw peers probe <name>` | — | Test peer connectivity |
| `maw peers list` | — | All registered peers |
| `maw peers info <name>` | — | Peer metadata (JSON) |
| `maw peers remove <name>` | — | Unregister peer |
| `maw discover` | — | List federation peers + tmux state |
| `maw ping <node>` | — | Federation health check |
| `maw pair generate` | — | Create 6-char ephemeral handshake |
| `maw pair <url> <code>` | — | Initiate pairing with 6-char code |
| `maw hey <node>:<oracle> "<msg>"` | — | Remote node addressing (federation) |
| `maw hey <node>:<session>:<window> "<msg>"` | — | Pick specific tmux window |

### Pane & Window Management

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw tile [N]` | — | Arrange current window into grid or spawn N panes |
| `maw tile --path <cwd> --cmd <cmd>` | — | Spawn + cd + boot in one verb |
| `maw bring <oracle>` | `b` | Bring oracle into current view (thin alias for `wake --split`) |
| `maw take <src:win> <dst>` | — | Move tmux window between oracle sessions |
| `maw promote <session:window>` | — | Eject window to standalone session |
| `maw open` | — | Bring back hidden panes (join-pane) |
| `maw close` | — | Hide panes without killing |
| `maw zoom <pane>` | — | Toggle zoom |
| `maw pane swap <a> <b>` | — | Reorder panes in current window |
| `maw panes` | — | List pane metadata across fleet |
| `maw view <agent>` | — | Read-only tmux view of agent's pane |

### Plugin Ecosystem

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw plugin ls` | — | Installed + tiered plugins |
| `maw plugin install <name>` | — | Install from registry or peers |
| `maw plugin install <path>` | — | Local directory (dev symlink) |
| `maw plugin install <url>` | — | HTTP(S) tarball |
| `maw plugin install <name>@<peer>` | — | Peer-to-peer discovery + install |
| `maw plugin install --force` | — | Replace existing install |
| `maw plugin install --pin` | — | Explicitly trust tarball hash |
| `maw plugin enable <name>` | — | Opt into disabled-but-installed tools |
| `maw plugin disable <name>` | — | Hide without uninstalling |
| `maw plugin remove <name>` | — | Uninstall |
| `maw plugin search <pattern>` | — | Search local registry |
| `maw plugin search <pattern> --peers` | — | Federated peer search |
| `maw plugin init <name>` | — | Create new plugin scaffold |
| `maw plugin init <name> --ts` | — | TypeScript scaffold |
| `maw plugin build <path>` | — | Package plugin as tarball |
| `maw plugin dev <path>` | — | Watch + test during development |

### Team Workspaces (Persistent)

| Command | Purpose |
|---------|---------|
| `maw team up <team>` | Spawn from `.maw/teams/<team>.yaml` charter |
| `maw team up <team> --dry-run` | Preview spawn plan |
| `maw team down <team>` | Graceful shutdown |
| `maw team create <name> [desc]` | Register team, invoking shell becomes lead |
| `maw team spawn <team> <role>@<cwd>[:<color>]` | Spawn team member via worktree |
| `maw team reassign <member> "#<issue>"` | Kill + fresh wake + re-dispatch |
| `maw team list` | All teams + status |
| `maw team status <team>` | Single team status |
| `maw team members <team>` | Team roster + inbox counts |
| `maw team add <team> <member>` | Add member to team |
| `maw team remove <team> <member>` | Remove member |
| `maw team send <team> <msg>` | Send message to team |
| `maw team resume <team>` | Reincarnation engine — restore from crash |
| `maw team oracle-invite <oracle:session> --team <name>` | Invite cross-machine oracle |
| `maw team oracle-remove <oracle> --team <name>` | Remove cross-machine member |

### Worktrees & Tasks

| Command | Purpose |
|---------|---------|
| `maw workon <repo>` | Create worktree (`--layout nested\|legacy`) |
| `maw workon <repo> --task "<brief>"` | Create worktree + send task |
| `maw workon <repo> --split` | Worktree side-by-side with current pane |
| `maw pulse add <name>` | Add task to pulse tracker |
| `maw pulse ls` | List active tasks |
| `maw pulse cleanup` | Prune completed tasks |
| `maw assign <issue-url>` | Assign issue to oracle |
| `maw inbox <oracle>` | Inbox management (read / approve / reject / drain) |

### Channels (Discord/Telegram/etc)

| Command | Purpose |
|---------|---------|
| `maw channel add <oracle> <type>` | Register channel (discord, telegram, etc) |
| `maw channel ls` | All configured channels |
| `maw channel remove <oracle> <type>` | Unregister channel |

**Auto-injection on wake**: If oracle has channel config at `~/.claude/channels/<oracle>/config.json`, `maw wake <oracle>` automatically injects `--channels`, `--continue`, and `--dangerously-skip-permissions`.

### Server & UI

| Command | Purpose |
|---------|---------|
| `maw serve [port]` | Start API server (default: 3456) |
| `maw ui install` | Download federation lens from maw-ui release |
| `maw ui install --version v1.15.0` | Specific version |
| `maw ui status` | Verify UI installation |
| `maw ui` | Open federation lens (http://localhost:3456/federation_2d.html) |
| `maw ui <peer>` | Lens pointed at peer's data |
| `maw ui --tunnel <host>` | SSH tunnel + lens URL |

### Monitoring & Diagnostics

| Command | Purpose |
|---------|---------|
| `maw doctor` | Version + plugins + dead agents + config checks |
| `maw doctor xdg` | Show active config/state/data/cache roots |
| `maw doctor xdg --migrate` | Copy legacy artifacts into XDG targets |
| `maw preflight` | Pre-flight: version, plugins, dead agents, config |
| `maw health` | Agent health summary |
| `maw costs` | Token/cost reporter |
| `maw on <oracle> <event>` | Listen for oracle events (`--once`, `--timeout`) |
| `maw snapshots list` | Browse wake snapshots |
| `maw snapshots show <id>` | Show snapshot details |

### Miscellaneous

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw contacts` | — | Persistent contact registry |
| `maw find` | — | Cross-fleet search |
| `maw overview` | — | Fleet-wide status |
| `maw transport` | `tp` | Transport layer status |
| `maw fck` | — | Command correction plugin |
| `maw swarm` | — | Multi-engine A/B panes |
| `maw avengers` | — | Multi-agent Avengers team framework |
| `maw mega` | — | MegaAgent multi-agent teams |
| `maw reunion` | — | Federation-wide reunion sync trigger |
| `maw scope` | — | Named routing namespaces |
| `maw tag` | — | Pane metadata for routing |
| `maw scaffold <name>` | — | Structure-only project creation |

---

## Configuration

### Primary Config: `~/.config/maw/maw.config.json`

```json
{
  "host": "local",
  "port": 3456,
  "bind": "0.0.0.0",
  "oracleUrl": "http://localhost:47779",
  
  "env": {
    "CLAUDE_CODE_OAUTH_TOKEN": "<token>"
  },
  
  "commands": {
    "default": "claude --dangerously-skip-permissions --continue",
    "*-oracle": "claude --dangerously-skip-permissions --continue",
    "codex-*": "codex --dangerously-auto-approve --search"
  },
  
  "sessions": {
    "nexus": "01-oracles",
    "hermes": "07-hermes"
  },
  
  "federationToken": "shared-secret-min-16-chars",
  "namedPeers": [
    { "name": "white", "url": "http://10.20.0.7:3456" }
  ]
}
```

**Load-bearing fields**:
- `host` — local node name
- `port` — API listen port
- `oracleUrl` — URL for external clients to reach this node
- `commands` — engine launch templates (precedence: exact match → wildcard → default)
- `federationToken` — HMAC-SHA256 signing secret (min 16 chars, symmetric)
- `namedPeers` — pre-configured remote nodes

**Optional**:
- `bind` — separate server bind address (e.g., `"0.0.0.0"` for federation, `"127.0.0.1"` for local only)
- `tmuxSocket` — custom tmux socket path
- `idleTimeoutMinutes` — agent auto-stop after idle
- `env` — environment variables injected into agent processes
- `engines` — generic engine definitions (dormant, Phase 2)

### XDG Runtime Paths

```bash
# Show active paths
maw doctor xdg

# New installs use:
# ~/.config/maw/              → config
# ~/.local/share/maw/         → data (XDG_DATA_HOME)
# ~/.cache/maw/               → cache
# ~/.local/state/maw/         → state

# Enable explicitly (opt-in)
MAW_XDG=1 maw doctor xdg
```

### Legacy paths (still readable, not written)
- `~/.config/maw/` — old config root
- `~/.maw/` — old all-in-one root

### Peers Configuration: `~/.maw/peers.json`

```json
{
  "peers": [
    { "alias": "alice", "url": "http://localhost:3457", "node": "alice", "nickname": "Alice Oracle", "lastSeen": "2026-04-19T10:42:07.512Z" }
  ]
}
```

### Plugin Registry Lock: `~/.maw/plugins.lock`

```json
{
  "plugin-name": {
    "source": "tarball | linked (dev) | registry",
    "hash": "sha256:9a34bd7c1f0e...",
    "version": "0.1.0"
  }
}
```

Used for tarball trust verification on install.

### Fleet Config: `~/.config/maw/fleet/<NN>-<name>.json`

```json
{
  "session": "101-mawjs",
  "windows": [
    { "name": "mawjs-oracle", "repo": "Soul-Brews-Studio/mawjs-oracle" }
  ],
  "sync_peers": ["mawjs-oracle"],
  "budded_from": "parent-oracle",
  "budded_at": "2026-04-10T03:50:00.000Z"
}
```

Generated by `maw bud`, tracks lineage.

### Team Charter YAML: `.maw/teams/<team>.yaml`

```yaml
name: my-team
description: A coordinated squad
members:
  - role: explorer
    engine: claude
    repo: my-workspace/repo-a
    prompt: "You are the explorer..."
  
  - role: builder
    engine: codex
    repo: my-workspace/repo-b
    prompt: "You are the builder..."

triggers:
  - on: agent-idle
    timeout: 300
    action: "maw hey {agent} 'ping'"
```

Drives `maw team up <team>` and reincarnation on crash.

### Channel Config: `~/.claude/channels/<oracle>/config.json`

```json
{
  "plugins": [
    {
      "id": "plugin:discord@claude-plugins-official",
      "env": {
        "DISCORD_STATE_DIR": "~/.claude/channels/mybot"
      }
    }
  ]
}
```

Bot token goes in `.env` alongside this file. Auto-injection on `maw wake <oracle>`.

---

## Plugin System

### Three-Tier Architecture

| Tier | Source | Load timing | Precedence | Examples |
|------|--------|-------------|-----------|----------|
| **Core** | `src/commands/plugins/` (bundled) | Symlinked every boot | Lowest | federation, inbox, health, doctor |
| **Vendored Registry** | `src/vendor/mpr-plugins/` (vendored) | Symlinked every boot | Low | wake, attach, done, send-enter |
| **User Installs** | `~/.maw/plugins/` or `MAW_PLUGINS_DIR` | Scanned at boot | **Highest** | Custom plugins, overrides |

**Precedence**: user name > vendored name > core name. First-run bootstrap only; symlinks idempotent.

### Plugin Manifest: `plugin.json`

```json
{
  "name": "myplugin",
  "version": "1.0.0",
  "entry": "./index.ts",
  "sdk": "^1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  
  "cli": {
    "command": "myplugin",
    "help": "maw myplugin <subcommand> [args]"
  },
  
  "weight": 10,
  "tier": "standard",
  
  "capabilities": ["hey", "peek", "team-create"],
  
  "hooks": {
    "wake": "./hooks/wake.ts",
    "serve": "./hooks/serve.ts",
    "sleep": "./hooks/sleep.ts"
  }
}
```

**Load-bearing fields**:
- `name`, `version`, `entry`, `sdk` — identity + boot
- `cli.command` — top-level command (e.g., `maw myplugin ...`)
- `weight` — display tier (0=core, 10=standard, 50=extra)

**Optional**:
- `capabilities` — advertised via federation `/info`
- `hooks` — lifecycle callbacks (wake/serve/sleep)

### Plugin Install Flow

```bash
# From registry (fetched on first run if not vendored)
maw plugin install hello

# From local dev dir (symlink)
maw plugin install ./hello --force

# From HTTP tarball
maw plugin install https://example.com/hello.tgz

# From peer (federated discovery)
maw plugin install hello@alice --pin

# SDK version check + extraction/symlink + hash lock
# Trust root: plugins.lock sha256, consent gate optional (#644 Phase 3)
```

### Plugin Development

```bash
# Scaffold
maw plugin init myplugin --ts

# Build tarball
cd myplugin
maw plugin build ./myplugin

# Install locally (dev symlink)
maw plugin install ./myplugin --force

# Watch + dev loop
maw plugin dev ./myplugin
```

### Plugin Tiers (Data-Driven from Usage)

| Range | Tier | Action |
|-------|------|--------|
| >200 invocations | **Core** | Keep enabled by default (8 plugins) |
| 50–200 | **Standard** | Keep enabled, watch for drift (13 plugins) |
| 20–50 | **Extra** | User opt-in OK (49 plugins) |
| <20 | **Lab/Zombie** | Candidate for `maw plugin disable` |
| 0 | **Dead** | Wire to workflow or lean out |

Example: `bud` has 486 invocations → extra tier. `artifact-manager` has 0 → dead candidate.

---

## Plugin Ecosystem

### Core Plugins (Weight 0)

| Plugin | Purpose | Status |
|--------|---------|--------|
| `federation` | Cross-machine primitives (HMAC auth, peer routing) | Active |
| `inbox` | Schema + persistent queues | Active |
| `health` | Agent health + status tracking | Active |
| `doctor` | Fleet diagnostics + repair | Active |
| `discover` | Scout federation state | Active |
| `oracle` | Identity + metadata | Active |
| `config` | Runtime config loader + validator | Active |
| `plugin` | Plugin lifecycle (init, build, install) | Active |

### Standard Plugins (Weight 10)

| Plugin | Purpose | Notes |
|--------|---------|-------|
| `team` | Persistent multi-agent charters + reincarnation | 23 subcommands |
| `team-agent` | Shell-only TeamCreate wrapper | Alternative to `/team-agents` |
| `tile` | Grid panes + spawn (`--path --cmd`) | Post-#1837: one verb |
| `pane` | Window/pane management (swap, zoom, close) | Tmux wrapper |
| `transport` | HTTP/WebSocket transport status | Diagnostics |
| `channel` | Discord/Telegram bot config | Auto-injection on wake |
| `tmux` | Tmux utilities | Session listing, cleanup |
| `cli` | Top-level dispatch + aliases | Core routing |
| `fleet` | Fleet inspection (list, sync, merge) | Heavy core ties |
| `swarm` | Multi-engine A/B panes | No coordination layer |
| `broadcast` | Fleet-wide fan-out | Light coupling |
| `avengers` | Multi-agent framework | Specialty workflow |
| `mega` | MegaAgent multi-agent teams | Alternative to team |

### Extra Plugins (Weight 50, Sample)

| Plugin | Purpose | Notes |
|--------|---------|-------|
| `bud` | Create new oracle | 486 invocations, heaviest |
| `done` | Finish worktree + cleanup session | Workflow-specific |
| `find` | Cross-fleet search | Touches ghq-root |
| `costs` | Token/cost reporter | Multi-source aggregation |
| `capture` | Workflow artifact capture | Fleet coupling |
| `archive` | Archive sessions | Soul-sync reach |
| `snapshot` | Wake state save/restore | Lifecycle |
| `about` | Oracle metadata blurb | SDK-only, light |
| `contacts` | Persistent contact registry | Schema coupling |
| `consent` | Trust gating for peer installs | Plugin-install gate |
| `pair` | Ephemeral federation pairing (6-char code) | Alternative to config |
| `reunion` | Federation-wide sync trigger | Cross-node ritual |
| `demo` | Demo runner | Easy lift candidate |

---

## Federation (Cross-Machine)

### Architecture

```
Node A (oracle-world)      Node B (white)         Node C (clinic-nat)
├── maw serve :3456   ┐    ├── maw serve :3456   ├── maw serve :3457
├── mawjs-oracle       │    ├── pulse-oracle     ├── neo-oracle
├── codec-oracle       │    └── ...              └── ...
└── ...                │
                       └─── peered via
                            namedPeers config +
                            HMAC-SHA256 signing
                            (port 3456 routable)
```

### Setup

**Step 1: Set federation token (symmetric, both sides)**

```bash
# On oracle-world
cat > ~/.config/maw/maw.config.json <<EOF
{
  "federationToken": "shared-secret-min-16-chars",
  "namedPeers": [
    { "name": "white", "url": "http://10.20.0.7:3456" }
  ]
}
EOF

# On white (same token)
cat > ~/.config/maw/maw.config.json <<EOF
{
  "federationToken": "shared-secret-min-16-chars",
  "namedPeers": [
    { "name": "oracle-world", "url": "http://10.20.0.1:3456" }
  ]
}
EOF
```

**Step 2: Verify peer handshake**

```bash
maw peers add white http://10.20.0.7:3456
maw peers probe white
# Expected: ✓ reached white
```

**Step 3: Use federation**

```bash
# Send message to remote oracle
maw hey white:neo "hello from oracle-world"

# Peek at remote screen
maw peek white:neo

# Broadcast to all named peers
maw broadcast "status update"

# Cross-node team invite
maw team oracle-invite white:neo --team my-team
```

### Addressing Format

```
[<node>:]<oracle>[:<session>][:<window>]

Examples:
  maw hey neo "msg"                  # local
  maw hey white:neo "msg"            # remote node + oracle
  maw hey white:neo:3 "msg"          # specific tmux window (#410)
```

### Federation API Endpoints (v1 Quartet)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `GET /api/config` | GET | Node identity + aggregated agents | None |
| `GET /api/fleet-config` | GET | Raw fleet/*.json (budded lineage) | None |
| `GET /api/feed?limit=N` | GET | Live event stream (messages, state) | None |
| `GET /api/federation/status` | GET | Peer reachability + latency | None |
| `POST /api/peer/exec` | POST | Signed command relay | HMAC-SHA256 |

**Critical note**: v1 auth is `none` on discovery endpoints. Do not tighten without coordinating with every lens in the mesh.

### Load-bearing v1 response fields

**`GET /api/config`**:
- `node` — local node name
- `agents` — `Record<agentName → nodeName>` (pre-aggregated)
- `namedPeers` — `Array<{name, url}>`

**`GET /api/fleet-config`**:
- `configs[].windows[].name` — agent name
- `configs[].budded_from` — parent (lineage)

**`GET /api/feed`**:
- `events[].event` — event kind (MessageSend, Notification, etc)
- `events[].oracle` — agent name
- `events[].ts` — unix millis (monotonic)

**`GET /api/federation/status`**:
- `peers[].reachable` — boolean
- `peers[].latency` — ms

### Peer Discovery & Plugin Install

**Federated search**:
```bash
maw plugin search ping --peers
# Searches local registry AND all peers (fan-out)
```

**Install from peer** (Shape A marketplace):
```bash
maw peers add alice http://localhost:3457
maw plugin search ping --peers
# Hit: ping@0.1.0 @alice

maw plugin install ping@alice --pin
# Federation query → hash verify → download → install
```

**Consent gate** (Phase 3, #644):
```bash
MAW_CONSENT=1 maw plugin install foo@untrusted
# Pending consent request written (out-of-band PIN delivery)

maw consent approve <id> <pin>
# Trust entry recorded, retryable
```

### Monitoring & Troubleshooting

```bash
maw federation                          # Status + control
maw peers list                          # All registered
maw peers info <name>                   # Metadata
maw ping <node>                         # Health check
maw discover                            # Scout state
maw locate <oracle>                     # Find across federation
```

---

## Team Workspaces

### Persistent Teams (`maw team`)

**Charter-driven** (YAML):
```bash
cat > .maw/teams/my-team.yaml <<EOF
name: my-team
description: A coordinated squad
members:
  - role: explorer
    engine: claude
    repo: path/to/repo-a
    prompt: "You are the explorer..."
  
  - role: builder
    engine: codex
    repo: path/to/repo-b
    prompt: "You are the builder..."
EOF

maw team up my-team              # Spawn from charter
maw team status my-team          # Current state
maw team send my-team "update"   # Broadcast to all
maw team down my-team            # Graceful shutdown
```

**Features**:
- Reincarnation engine — if pane dies, `maw team resume` restores from registry
- Worktree isolation — each member gets isolated git worktree
- Cross-machine via `oracle-invite`
- 26+ concurrent teams proven (2026-05-14)
- Persistent inbox per member

**Subcommands** (23 total):
- **Lifecycle**: `create`, `spawn`, `spawn-from`, `bring`, `send`, `shutdown`, `resume`, `lives`
- **Setup**: `plan`, `preflight`, `load`
- **Status**: `list`, `status`, `members`
- **Tasks**: `add`, `tasks`, `done`, `assign`
- **Federation**: `oracle-invite`, `oracle-remove`

### Ephemeral Teams (Claude Code API)

**In-process** (single session, not persistent):
```typescript
// Via TeamCreate + SendMessage
teamId = await TeamCreate({ name: "squad", members: ["role1", "role2"] });
await SendMessage({ to: "role1@squad", payload: { task: "..." } });
```

**Benefits**:
- In-memory, no disk persistence
- 3-tier fallback (tmux → in-process → subagents)
- Heartbeat protocol mandatory (PROGRESS/STUCK/DONE/ABORT)
- Task graph coordination via TaskCreate/TaskUpdate

**Compared to `maw team`**:
- `maw team` — persistent, fleet-level, reincarnation
- `/team-agents` (Claude Code skill) — ephemeral, session-level, heartbeat

---

## Channel Integration (Discord/Telegram)

### Setup

```bash
# 1. Create channel state dir
mkdir -p ~/.claude/channels/mybot

# 2. Add bot token
echo 'DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN' > ~/.claude/channels/mybot/.env

# 3. Configure access (access.json)
cat > ~/.claude/channels/mybot/access.json <<EOF
{
  "dmPolicy": "allowlist",
  "allowFrom": ["<user-id>"],
  "groups": {
    "<channel-id>": {
      "requireMention": false,
      "allowFrom": ["<user-id>"]
    }
  },
  "pending": {}
}
EOF

# 4. Register the channel
maw channel add mybot discord

# 5. Wake
maw wake mybot
```

### Auto-Injection on Wake

When `maw wake <oracle>` detects channel config at `~/.claude/channels/<oracle>/config.json`:

```bash
DISCORD_STATE_DIR=~/.claude/channels/mybot \
  claude --dangerously-skip-permissions --continue \
         --channels plugin:discord@claude-plugins-official
```

Three flags injected automatically:
- `--channels plugin:discord@...` — connects to Discord API
- `--dangerously-skip-permissions` — bot runs autonomous (no prompts)
- `--continue` — retains context across restarts

### Managing Channels

```bash
maw channel add <oracle> discord      # Register
maw channel add <oracle> telegram     # Different platform
maw channel ls                        # All configured
maw channel remove <oracle> discord   # Unregister
```

---

## The `maw bud` Command (Oracle Creation)

### CLI Signature

```bash
maw bud <name>                      # Root oracle
maw bud <name> --from <parent>      # Budded from parent
maw bud <name> --org <org>          # Target different GitHub org
maw bud <name> --repo <org/proj>    # Seed from existing project's ψ/
maw bud <name> --issue <n>          # Tie to GitHub issue
maw bud <name> --fast               # Skip wake step
maw bud <name> --note "why"         # Birth note → ψ/memory/learnings/
maw bud <name> --dry-run            # Plan without executing
```

### What It Does (7 Steps)

1. **Validate name** — regex `^[a-zA-Z][a-zA-Z0-9-]*$`
2. **Resolve parent** — from `--from`, inherit sync_peers + lineage
3. **Resolve target org** — precedence: `--org` → config → `Soul-Brews-Studio`
4. **Create repo** — `gh repo create <org>/<name>-oracle` (idempotent)
5. **Write CLAUDE.md** — identity template + Rule 6 reminder
6. **Initialize ψ/ vault** — brain structure (memory, inbox, outbox, resonance, traces)
7. **Fleet config + commit** — writes `~/.config/maw/fleet/<NN>-<name>.json`, seeds git

### Output Artifacts

```
<name>-oracle/
├── CLAUDE.md                          # Identity template
├── ψ/
│   ├── memory/
│   │   ├── learnings/                 # Birth note (if --note given)
│   │   ├── resonance/                 # Patterns + emotional logs
│   │   └── traces/                    # Search logs
│   ├── inbox/
│   │   └── handoff/                   # Session handoffs
│   └── outbox/                        # Pending items
└── (git repo initialized)
```

### Usage Data (Invocations)

| Metric | Count |
|--------|-------|
| Total `maw bud` invocations | 486 |
| From `--from <parent>` | ~300 (61%) |
| Root buds (`--root` or no parent) | ~70 (14%) |
| Help/testing runs | ~116 (24%) |
| Actual budding events (est.) | ~370 |

**Selection pressure**: Budding is the 3rd most-used command after `hey` (3,043) and `wake` (648).

---

## Vault Structure (ψ/)

Every oracle repo includes a `ψ/` brain directory:

```
ψ/                                      # Psi — the oracle's brain
├── memory/
│   ├── resonance/                      # Soul, identity, patterns
│   ├── learnings/                      # Lessons + discoveries
│   │   └── YYYY-MM-DD_birth-note.md   # Created by maw bud --note
│   ├── traces/                         # Session search logs
│   └── retrospectives/                 # Session reflections
├── inbox/
│   ├── handoff/                        # Session-to-session transfers
│   └── <user-name>/                    # Per-user message queues
├── outbox/                             # Pending to other oracles
├── writing/                            # Drafts in progress
├── lab/                                # Experiments
├── learn/                              # Deep-learned repos
├── archive/                            # Completed work
└── <reference-data>/                   # Domain-specific reference
```

Used by oracles for memory persistence across sessions, handoffs between humans, and soul-syncs with parent oracles.

---

## Wake Lifecycle

### Steps in `maw wake <oracle>`

1. **Resolve oracle** — exact match or fuzzy search
2. **Check fleet config** — load session slot from `~/.config/maw/fleet/`
3. **Ensure session exists** — create tmux session or reuse
4. **Auto-clone if needed** — `ghq get` via GitHub if repo missing locally
5. **Plugin wake hooks** — `hooks.wake` from `plugin.json`
6. **Build command** — engine + channel flags + prompt
7. **Spawn pane** — `tmux new-window` + `send-keys`
8. **Drain inbox** — deliver any queued messages
9. **Attach or split** — `attach-session` or `split-window -h`

### Dry Run & Preview

```bash
maw wake neo --dry-run              # Show plan without executing
maw wake --list                     # Show available agents
maw wake --from-snapshot <id>       # Restore from previous state
```

### Snapshots (Wake State)

```bash
maw snapshots list                  # Browse captured states
maw snapshots show <id>             # Show details
maw wake neo --from-snapshot <id>   # Restore
```

---

## Communication Convention

### Channels

| Channel | Command | Format | Delivery |
|---------|---------|--------|----------|
| **hey** | `maw hey <target> "msg"` | Identity-signed envelope | tmux inject + Enter (local or federation) |
| **talk-to** | `maw talk-to <target> "msg"` | Thread (MCP) + tmux | Persistent conversation |
| **inbox** | `maw hey --inbox <target> "msg"` | File-based queue | No pane injection (async) |
| **team** | `maw hey team:<name> "msg"` | Fan-out | Individual delivery to each member |

### Message Format

```
[node:sender] message content here
```

- Slash commands (`/skill`, `$cmd`) preserved as-is
- Already-signed messages pass through unchanged
- Auto-delivery queue respects target status (busy → queue, idle → inject)

### Status-Aware Delivery

| Target Status | Behavior |
|---------------|----------|
| **ready** | Direct injection |
| **idle** | Direct injection |
| **busy** | Queued for auto-delivery on transition |
| **crashed** | Inbox queue |
| **unknown** | Direct injection (no guard) |

---

## Runtime Paths & Environment

### Default Paths

```
~/.config/maw/              # Config (primary)
~/.local/share/maw/         # Data (XDG_DATA_HOME)
~/.cache/maw/               # Cache
~/.local/state/maw/         # State

~/.maw/                     # Legacy (still readable)
~/.config/maw/fleet/        # Fleet configs
~/.maw/plugins/             # User plugin installs
~/.maw/peers.json           # Peer registry
~/.maw/plugins.lock         # Plugin hash trust
~/.maw/oracle.json          # Node identity
~/.maw/peer-manifest-cache/ # Peer plugin cache
~/.maw/consent/             # Consent requests + trust

~/.claude/channels/<oracle>/ # Channel state
  ├── .env                   # Bot tokens
  ├── config.json            # Channel plugins
  └── access.json            # Discord access control
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `MAW_HOME` | Override all paths (dev/testing) |
| `MAW_XDG` | Opt into XDG spec (new installs) |
| `MAW_PLUGINS_DIR` | Override plugin scan directory |
| `MAW_CONSENT` | Enable consent gating for peer installs |
| `DISCORD_STATE_DIR` | Discord bot state location |
| `DISCORD_BOT_TOKEN` | Discord bot auth token |

---

## Docker & Testing

### Federation Testing (Two-node mesh)

```bash
# Spin up containers on shared network + run smoke test
bash scripts/test-docker-federation.sh   # build + up + probe + teardown

# Or leave running
bash scripts/dev-federation.sh up        # stays running for dev
bash scripts/dev-federation.sh down      # teardown when done
```

Runs `maw peers probe` both directions as round-trip validation. CI runs via `.github/workflows/federation-docker.yml` on PRs touching transports or federation.

---

## Plugin Creation Walkthrough

### Scaffold

```bash
maw plugin init myplugin --ts
cd myplugin
```

### Manifest (`plugin.json`)

```json
{
  "name": "myplugin",
  "version": "0.1.0",
  "entry": "./index.ts",
  "sdk": "^1.0.0",
  "description": "Does something useful",
  "author": "You",
  "cli": {
    "command": "myplugin",
    "help": "maw myplugin [args]"
  },
  "weight": 50
}
```

### Entry Point (`index.ts`)

```typescript
import { definePlugin } from "maw-sdk";

export default definePlugin((hooks) => {
  hooks.on("*", (event) => {
    console.log(`Event: ${event.type}`);
  });
});
```

### Build & Install

```bash
maw plugin build ./myplugin          # → myplugin-0.1.0.tgz

maw plugin install ./myplugin        # dev symlink

# Or package for distribution
maw plugin install ./myplugin-0.1.0.tgz --pin  # tarball + hash lock
```

### Dev Loop

```bash
maw plugin dev ./myplugin            # watch + test
```

---

## Lean-Core Philosophy

**Principle**: Core must ship with zero network dependencies. Vendored registry plugins ensure fresh installs work offline; optional registry sources are one-time bootstrap on demand.

**Three-tier strategy**:
1. **Core** (8 plugins) — federation, inbox, plugin loader, identity, config
2. **Standard** (13 plugins) — health, lifecycle, peer discovery
3. **Extra** (49+ plugins) — specialized workflows, opt-in

**Data-driven tiers**: Plugin `weight` assigned from 6-month usage audit (3,043 `hey` invocations vs. 0 `artifact-manager` = 0 weight).

**Extraction path**: Clean plugins (SDK-only coupling) fast-tracked for community repos. Tangled plugins stay in-tree until SDK widening. Reference: `shellenv` (#816), `rename` (#859).

---

## Known Limitations & Open Gaps

1. **Registry blindness** — L2 teams (`/team-agents` in Claude Code) invisible to L1 `maw ls`. Two registries, no sync.
2. **Naming collision** — `/team-agent` (singular) vs `/team-agents` (plural) easy to mistype.
3. **`maw buddy` incomplete** — Scaffold exists in `maw-plugin-registry`, fixtures + tests pending (maw-plugin-registry#94).
4. **No `--parent-session-id` flag** — Spawned agents don't auto-discover spawner (workaround: env or system prompt).
5. **Consent gating** — Phase 3 of #644 still in flight (Phase 1 shipped, integration pending).
6. **Cross-node buddy blocked** — Depends on #1814 (identity collision) fix.

---

## Version & CalVer

**Versioning scheme**: CalVer `v{yy}.{m}.{d}[-alpha.{HHMM}]`

- `v26.5.17-alpha.752` = 2026-05-17, alpha build 0752 (built 07:52)
- `v26.5.20` = 2026-05-20, stable release
- Migrated from SemVer on 2026-04-18 (issue #526)

**Timeline**:
- Oct 2025: `maw.env.sh` (shell commands)
- Mar 2026: `maw.js` (Bun/TS rewrite)
- Apr 2026: v2.0.0-alpha.66 (plugin OS foundation)
- May 2026: v26.5.20-alpha.2203 (teams, federation, 89 plugins)
- Jun 2026: v26.6.6-alpha.1830 (charters, lean-core extraction)

---

## Further Reading

- **Federation docs**: `/docs/federation/getting-started.md` (peer setup, handshake errors)
- **Teams deep-dive**: `/docs/teams.md` (20+ coordination verbs, architectural seams)
- **Plugin marketplace**: `/docs/plugins/shape-a-demo.md` (7-step walkthrough, Shape A)
- **Installation recovery**: `/docs/install-recovery.md` (name collision fix, bootstrap)
- **Communication convention**: `/docs/communication-convention.md` (channels, delivery, API)
- **Lean-core audit**: `/docs/lean-core/plugin-audit.md` (tier classification, extraction)
- **Wake channels runbook**: `/docs/wake-channels-runbook.md` (Discord/Telegram bots)
- **Bud command**: `/docs/bud.md` (oracle creation, usage audit, 486 invocations)

**Main repo**: https://github.com/Soul-Brews-Studio/maw-js  
**UI repo**: https://github.com/Soul-Brews-Studio/maw-ui  
**Plugin registry**: https://github.com/Soul-Brews-Studio/maw-plugin-registry
