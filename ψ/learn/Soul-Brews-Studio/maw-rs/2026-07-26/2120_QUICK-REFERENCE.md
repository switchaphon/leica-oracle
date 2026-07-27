# maw-rs Quick Reference

**Repository**: Soul-Brews-Studio/maw-rs  
**Branch**: alpha  
**Built**: 2026-07-26  
**Latest Release**: CalVer tagged releases (e.g., v26.7.16)

> Distributed terminal multiplexing & fleet management for AI agent oracles — Rust port of maw-js.

---

## Installation

### Homebrew (macOS Apple Silicon)
```bash
brew install soul-brews-studio/maw/maw
maw --version
```

### Release Installer (Recommended)
**Stable channel**:
```bash
curl -fsSL https://github.com/Soul-Brews-Studio/maw-rs/releases/latest/download/install.sh | sh
```

**Bleeding-edge (alpha)**:
```bash
curl -fsSL https://raw.githubusercontent.com/Soul-Brews-Studio/maw-rs/alpha/install.sh | sh
```

**Pin to specific CalVer release** (e.g., v26.7.16):
```bash
MAW_VERSION=v26.7.16 sh install.sh
# or
curl -fsSL https://github.com/Soul-Brews-Studio/maw-rs/releases/download/v26.7.16/install.sh | sh
```

**Installation options**:
```bash
INSTALL_DIR="$HOME/bin" sh install.sh
sh install.sh --version v26.7.16 --install-dir "$HOME/bin"
```

### Build from Source
Requires Rust toolchain:
```bash
cargo install --path crates/maw-cli --features wasm-host
ln -sf "$(command -v maw-rs)" "$HOME/.local/bin/maw"
```

Lean build (no WASM plugin support):
```bash
cargo install --path crates/maw-cli
```

### Supported Platforms
- **macOS Apple Silicon** (`maw-rs-macos-arm64`) — prebuilt binary
- **Linux x86_64** (`maw-rs-linux-x86_64-musl`) — static binary

**Note**: If Gatekeeper blocks the macOS binary:
```bash
xattr -d com.apple.quarantine ~/.local/bin/maw
```

---

## Configuration

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MAW_XDG=1` | Enable XDG-compatible paths (recommended) | `export MAW_XDG=1` |
| `XDG_CONFIG_HOME` | Config directory (if XDG enabled) | `$HOME/.config` |
| `XDG_STATE_HOME` | State directory (if XDG enabled) | `$HOME/.local/state` |
| `MAW_HOME` | Legacy home directory (XDG_disabled) | `$HOME/.maw` |
| `MAW_STATE_DIR` | Override state directory | `/tmp/maw-state` |
| `MAW_INSTANCE` | Instance name for multi-user tmux | `my-instance` |
| `MAW_X_DEBUG=1` | Enable debug output for `maw x` | `export MAW_X_DEBUG=1` |
| `TMUX_PANE` | Current pane (set by tmux) | `%0` |

### Config Paths

**XDG-enabled** (recommended, set `MAW_XDG=1`):
```
~/.config/maw/           # config
~/.local/state/maw/      # state / sessions / plugins
~/.cache/maw/            # plugin cache / temp
```

**Legacy paths** (without `MAW_XDG`):
```
~/.maw/                  # all state + config
```

**Config file** (merged from layers):
```
$XDG_CONFIG_HOME/maw/maw.json  (XDG-enabled)
~/.maw/maw.json                (legacy)
```

**Discovery order** (later layers override earlier):
1. System defaults
2. User-wide config
3. Project-scoped config (in repo `.maw/` directory)
4. Runtime env vars

---

## Command Reference

### Top-Level Commands

#### Help & Versioning

| Command | Alias | Purpose |
|---------|-------|---------|
| `maw --help` | `-h`, `help` | Show usage |
| `maw --version` | `-v`, `version` | Show build version & commit |
| `maw commands` | — | List all available commands |
| `maw completions zsh` | — | Generate zsh completions |

#### Session & Fleet Management

| Command | Purpose | Common Flags |
|---------|---------|--------------|
| `maw ls` | List sessions, windows, panes (tmux) | `--json` |
| `maw a <target>` | Attach to session (alias: `attach`) | `--readonly` / `-r` |
| `maw team up` | Start fleet (create sessions) | `--dry-run`, `--print-json` |
| `maw team down` | Shutdown fleet | `--force`, `--dry-run` |
| `maw fleet sync` | Synchronize config across fleet | `--dry-run`, `--check` |
| `maw fleet health` | Check fleet status | `--json` |
| `maw fleet gc` | Garbage collect orphaned sessions | `--dry-run` |
| `maw workon <repo>` | Spawn agent in worktree | `--wt`, `--fresh`, `--engine <e>`, `--layout nested\|legacy`, `--name`, `-e <engine>` |

#### Tmux Pane Operations

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw t <repo> <slug>` | Spawn new tab/window | `maw t <repo> <slug>` |
| `maw s <target>` | Split pane (horizontal) | `maw s <target>` |
| `maw tmux split <pane>` | Split pane (tmux subcommand) | `maw tmux split <pane>` |
| `maw tmux layout` | Manage layout | `maw tmux layout <layout>` |
| `maw tmux attach <pane>` | Attach to pane | `maw tmux attach <target>` |
| `maw tmux open <session>` | Create new session | `maw tmux open <name>` |
| `maw tmux close <target>` | Kill pane | `maw tmux close <target>` |
| `maw tmux break <pane>` | Break pane into new window | `maw tmux break <pane> [--force]` |
| `maw tmux sync` | Synchronize panes | `maw tmux sync <target>` |
| `maw tmux peek <pane>` | View pane content | `maw tmux peek <target>` |
| `maw tmux pipe <pane>` | Pipe pane to command | `maw tmux pipe <target> <cmd>` |
| `maw tmux ls` | List tmux state | — |
| `maw tmux kill` | Force kill tmux | `maw tmux kill <target>` |

#### Communication

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw hey <session:window.pane> "<message>"` | Send text to pane | `maw hey target "message"` |
| `maw send-text <target> <text>` | Send text (alias) | Same as `hey` |
| `maw send-key <target> <key>` | Send key press | `maw send-key target C-c` |
| `maw send-enter <target>` | Send Enter key | `maw send-enter target` |
| `maw send-escape <target>` | Send Escape key | `maw send-escape target` |
| `maw notify <session> "<message>"` | Desktop notification | `maw notify 50-main "done"` |

#### Workspace & Worktree

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw workspace` | Workspace operations | `maw workspace [subcommand]` |
| `maw worktree` | Worktree operations | `maw worktree [subcommand]` |
| `maw worktree-window` | Worktree window query | `maw worktree-window <target>` |
| `maw finish <worktree>` | Mark worktree done | `maw finish <wt>` |
| `maw park <worktree>` | Temporarily close worktree | `maw park <wt>` |

#### Plugin System

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw x <spec>` | Run plugin/spec | `maw x <spec> [--sha256 <hex>] [-y\|--yes] [--offline] [--dry-run]` |
| `maw x ls` | List cached plugins | — |
| `maw x gc` | Garbage collect cache | `maw x gc [--max-age 30d] [--max-size 500m] [--dry-run]` |
| `maw x rm <verb>` | Remove cached plugin | `maw x rm <verb\|artifact\|sha256>` |
| `maw x trust ls` | List trust rules | — |
| `maw x trust revoke <source>` | Revoke trust | `maw x trust revoke <source>` |
| `maw plugin create` | Scaffold new plugin | `maw plugin create --rust <name>` |
| `maw plugin build` | Build WASM plugin | — |

#### Discovery & Routing

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw discover` | Discover repos, worktrees | `maw discover [<path>]` |
| `maw find` | Find target by query | `maw find <query>` |
| `maw resolve <target>` | Resolve target reference | `maw resolve <target> [--json]` |
| `maw route <target>` | Route to target | `maw route <target> [--json]` |
| `maw scope` | Show current scope | — |
| `maw scope find <query>` | Find in scope | `maw scope find <query>` |

#### Monitoring & Debugging

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw activity` | Show activity feed | `maw activity [<lines>] [--json]` |
| `maw ping` | Ping self & peers | `maw ping [--json]` |
| `maw whoami` | Show identity | `maw whoami [--json]` |
| `maw health` | System health check | — |
| `maw doctor` | Diagnose issues | — |

#### Federation & Peers

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw federation init` | Initialize federation | `maw federation init <node-id>` |
| `maw federation sync` | Sync federation state | `maw federation sync [--force] [--prune] [--dry-run]` |
| `maw federation health` | Check federation health | `maw federation health [--json]` |
| `maw federation identity` | Show federation identity | — |
| `maw peer probe` | Probe peer | `maw peer probe <host:port> [--json]` |
| `maw peer-sources` | List peer sources | — |
| `maw peers` | List all peers | `maw peers [--json]` |

#### Consent & Trust

| Command | Purpose | Syntax |
|---------|---------|--------|
| `maw consent request` | Request consent | — |
| `maw consent trust-check` | Check trust status | — |
| `maw consent trust-revoke <peer>` | Revoke peer trust | — |
| `maw pair code` | Generate pairing code | — |
| `maw pair api` | API pairing | — |
| `maw pair auto` | Auto-pairing | — |

#### Version & Update

| Command | Purpose |
|---------|---------|
| `maw update` | Check for updates |
| `maw upgrade` | Download & install update |

#### Advanced / Internal

| Command | Purpose | Notes |
|---------|---------|-------|
| `maw oracle` | Oracle operations | Specialist agent support |
| `maw team` | Team lifecycle | Subcommands: `up`, `down`, `enter`, `remove`, etc. |
| `maw on` | Event listener | Registry pattern |
| `maw wave` | Broadcast message | Fleet-wide notifications |
| `maw fulfill` | Plugin fulfillment | Ship-tier WASM runner |
| `maw talk-to` / `maw talkto` | Peer communication | Direct peer messaging |
| `maw zenoh-scout` | Zenoh peer discovery | P2P scout (experimental) |

---

## Tmux Subcommands

Run as `maw tmux <subcommand>`:

| Subcommand | Purpose | Syntax |
|------------|---------|--------|
| `attach` | Attach to pane/session | `maw tmux attach <target>` |
| `break` | Break pane to window | `maw tmux break <pane> [--force]` |
| `close` | Kill pane or window | `maw tmux close <target>` |
| `kill` | Force kill tmux | `maw tmux kill <server>` |
| `layout` | Configure layout | `maw tmux layout <layout>` |
| `ls` | List panes | — |
| `open` | Create new session | `maw tmux open <name>` |
| `peek` | View pane content | `maw tmux peek <target>` |
| `pipe` | Pipe pane output | `maw tmux pipe <target> <cmd>` |
| `split` | Split pane | `maw tmux split <pane>` |
| `sync` | Synchronize panes | `maw tmux sync <target>` |

---

## Fleet Subcommands

Run as `maw fleet <subcommand>`:

| Subcommand | Purpose | Flags |
|------------|---------|-------|
| `add` | Add session to fleet | — |
| `census` | Fleet configuration audit | `--json` |
| `doctor` | Diagnose fleet issues | — |
| `gc` | Garbage collect | `--dry-run` |
| `health` | Fleet health | `--json` |
| `init` | Initialize fleet | — |
| `consolidate` | Merge sessions | — |
| `resume` | Resume fleet | `--all` |
| `sync` | Sync config | `--dry-run`, `--check`, `--force` |
| `wake` | Wake fleet | — |
| `sleep` | Hibernate fleet | — |
| `gather` | Gather agents | — |
| `renumber` | Renumber sessions | — |

---

## Common Flags & Options

### Global Flags

| Flag | Purpose |
|------|---------|
| `--help` / `-h` | Show help for command |
| `--version` / `-v` | Show version |
| `--json` | Output as JSON (most commands) |
| `--dry-run` | Plan without executing |
| `--print` / `--print-json` | Show plan (JSON) |
| `--force` | Skip confirmation |
| `--quiet` / `-q` | Suppress output |
| `--debug` | Verbose logging |

### Target Selection

Targets reference tmux sessions, windows, and panes:
```
<session>              # session name or index
<session>:<window>     # specific window
<session>:<window>.<pane>  # specific pane
```

Abbreviations work with fuzzy matching:
```
maw a maw      # attach to session matching "maw"
maw hey dev "test"  # send to pane in session matching "dev"
```

### Workon Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--wt [<name>]` | Use/create worktree | `maw workon <repo> --wt myfeature` |
| `--fresh` / `--new` | Fresh worktree | `maw workon <repo> --fresh` |
| `--name <slug>` | Session name | `maw workon <repo> --name my-session` |
| `-e` / `--engine <e>` | Spawn engine | `maw workon <repo> -e codex` |
| `--layout nested \| legacy` | Session layout | `maw workon <repo> --layout legacy` |

### Plugin (X) Flags

| Flag | Purpose |
|------|---------|
| `--sha256 <hex>` | Verify plugin hash |
| `-y` / `--yes` | Auto-approve trust |
| `--offline` / `--frozen` | Use cache only |
| `--reload` | Ignore cache |
| `--from <spec>` | Dependency injection |
| `--registry <owner/repo>` | Plugin registry |
| `--remote` | Bypass local shadow |
| `--install` | Persist in plugins.lock |
| `--force` | Override existing |
| `--dry-run` | Show plan |
| `--` | Separate maw args from plugin args |

---

## Verified Commands (User-Facing Surface)

Based on source code inspection (crates/maw-cli/src/core_impl/):

### Verified Existing
✅ **`maw workon`** — EXISTS  
Source: `workon.rs` (DISPATCH_49)  
Usage: `maw workon <repo> [--wt [<name>]] [--fresh] [--name <slug>] [-e <engine>] [--layout nested|legacy]`

✅ **`maw hey`** — EXISTS  
Source: `send_text.rs` (DISPATCH_84)  
Usage: `maw hey <target> "<text>"`  
Aliases: `send-text`, `maw send-text`

✅ **`maw team`** — EXISTS  
Source: `team_core.rs` (DISPATCH_xxx)  
Subcommands: `up`, `down`, `enter`, `remove`, `shutdown`, `delete`, etc.

✅ **`maw done`** — EXISTS  
Source: (part of lifecycle management)

✅ **`maw ls`** — EXISTS  
Source: `session_list_plan.rs`  
Usage: `maw ls [--json]`

✅ **`maw fleet sync`** — EXISTS  
Source: `fleet.rs` (DISPATCH_61)  
Usage: `maw fleet sync [--dry-run] [--check] [--force]`

✅ **`maw codex`** (via `maw more codex`)  
Source: `more.rs` (DISPATCH_324)  
Usage: `maw more codex [N] [--session <s>] [--dry-run] [-e|--engine <e>]`  
Note: Access via `more` command, not direct `codex` command

### Capture / Peek
✅ **`maw capture`** — EXISTS (native, top-level)  
Source: `crates/maw-cli/src/core_impl/capture.rs:1-4` — `DISPATCH_77`, `command: "capture"`, `Handler::Sync(capture_run_command)`  
Usage: `maw capture <target> [--pane N] [--lines N] [--full]`  (`capture.rs:92`)

✅ **`maw peek`** — EXISTS (tmux subcommand)  
Source: `tmux_peek.rs`  
Usage: `maw peek <pane>` or `maw tmux peek <target>`

### Note on Capture vs Peek
- `maw capture` is a first-class native command, signature-compatible with maw-js usage
- `maw peek` is the quick-glance variant; capture's own help points to it
  (`"(see: maw peek for quick glance)"`)

> **Correction (verified by Leica, 2026-07-26):** an earlier draft of this file
> recorded `maw capture` as NOT FOUND. That was wrong — it is registered natively
> as `DISPATCH_77`. Verified directly against source before publishing.

---

## Architecture Notes

### Command Dispatch
- **System**: Custom dispatch via `DispatcherEntry` structs in core_impl modules
- **Build-time**: `build.rs` generates dispatch tables from `DISPATCH_NN` constants
- **Pattern**: Each command file defines dispatcher entry + implementation
- **Async support**: Tokio runtime with async handler support (see `discord` command)

### Plugin Runtime
- **WASM Host**: Extism-based (requires `--features wasm-host`)
- **Install path**: `~/.local/state/maw/plugins/` (XDG) or `~/.maw/plugins/` (legacy)
- **Manifest**: `plugin.json` per plugin directory
- **Dry-run**: `maw x <spec> --dry-run` shows resolved plugin plan without execution

### Tmux Integration
- **Transport**: Direct tmux CLI via `CommandTmuxRunner`
- **Session syntax**: `[<number>-]<name>[:<window>[.<pane>]]`
- **Attach fast-path**: Main process (`main.rs`) optimizes `attach` to direct tmux exec

### XDG Compliance
- **Detection**: `MAW_XDG=1` environment variable (or auto-detected)
- **Mandatory on Linux**: Strongly recommended for portability
- **Legacy support**: `~/.maw/` fallback for backwards compatibility

---

## Troubleshooting

### Common Issues

**Command not found**: Run `maw commands` to list all available commands

**Plugin trust blocked**: Use `-y` flag or `maw x trust ls` to approve

**Tmux attach fails**: Ensure tmux is running; check `maw ls` for session state

**Worktree creation fails**: Verify git repo exists and `--wt` slug is valid

**XDG paths not working**: Ensure `MAW_XDG=1` is set; check `maw xdg` output

### Debug Mode

Enable verbose output:
```bash
maw x ls --debug           # Plugin cache debugging
MAW_X_DEBUG=1 maw x run spec  # Trace plugin resolution
maw --debug ls             # General CLI debug
```

---

## Release & Build Info

**Build Metadata** (embedded at compile time):
- Version: `MAW_BUILD_VERSION` (CalVer: `26.MMDD.PATCH`)
- Git commit: `MAW_RS_GIT_HASH`
- Date: `MAW_RS_BUILD_DATE`

Display via:
```bash
maw --version              # Full version string with commit
maw version                # Same as --version
```

**CI/CD**:
- Stable releases: GitHub Actions via `.github/workflows/`
- Homebrew formula: `soul-brews-studio/homebrew-maw` tap
- Installer: `install.sh` (SHA-256 verified)

---

## References

- **Repository**: https://github.com/Soul-Brews-Studio/maw-rs
- **Branch**: `alpha` (development), `main` (stable)
- **Releases**: https://github.com/Soul-Brews-Studio/maw-rs/releases
- **Homebrew**: `soul-brews-studio/maw`
- **Issue tracking**: GitHub Issues in Soul-Brews-Studio/maw-rs

---

**Generated**: 2026-07-26  
**maw-rs branch**: alpha  
**Scope**: User-facing CLI surface & configuration
