# maw-rs Architecture Analysis

**Date**: 2026-07-26  
**Repo**: https://github.com/Soul-Brews-Studio/maw-rs (alpha branch)  
**Status**: Phase 1 complete — workspace scaffolded with portable fixtures. Phase 2 underway — side-effecting transport implementations. Phase 3 planned — CLI command porting.

---

## Overview

**maw-rs** is a Rust port of **maw-js** — a distributed terminal multiplexing & fleet management system for AI agent oracles. It's a layered Cargo workspace designed for deterministic core logic that ports to both native Rust and WebAssembly plugin execution.

**Key Design Principles**:
1. **Deterministic leaf crates** — Core logic is pure, side-effect-free, validated against JSON fixtures from maw-js
2. **Layered composition** — Leaf → Mid → Top (CLI) dependencies flow one direction
3. **External extraction** — Eleven extracted leaf crates live in separate repos (maw-crates, maw-calver), consumed as pinned Cargo git dependencies
4. **Plugin-first surfaces** — Fleet plugins run in Extism WASM; native code is slim
5. **No unsafe code** — Workspace forbids `unsafe_code` by lint

---

## Workspace & Crate Structure

### Directory Layout

```
maw-rs/
├── crates/                          # 13 local crates
│   ├── maw-matcher/                 # Target resolution (match/normalize)
│   ├── maw-worktree/                # Worktree/window matching logic
│   ├── maw-transport/               # Transport routing & failure handling
│   ├── maw-schedule/                # Schedule manifest parsing (TOML)
│   ├── maw-schedule-launchd/        # macOS launchd schedule adapter
│   ├── maw-schedule-runner/         # Schedule execution primitives
│   ├── maw-tmux/                    # tmux parsing & session discovery
│   ├── maw-peer/                    # Peer/oracle identity resolution
│   ├── maw-auth/                    # Federation auth (HMAC-SHA2, ed25519)
│   ├── maw-xdg/                     # XDG path resolution (macOS-aware)
│   ├── maw-plugin-manifest/         # WASM plugin manifest + Extism host
│   ├── maw-cli/                     # Main binary & HTTP gateway (see below)
│   └── maw-discord/                 # Discord bot integration (Twilight SDK)
├── docs/                            # Design docs, guides, parity tracking
│   ├── design/                      # Architecture proposals (WASM, native-schedule, federation)
│   ├── guides/                      # Procedural docs (add command, release, gating)
│   ├── parity/                      # maw-js → maw-rs command parity matrix
│   ├── reference/                   # Technical specs (wire protocol, plugin invoke)
│   └── principles/                  # Fleet intelligence principles
├── packages/
│   └── wasm-sdk/                    # AssemblyScript WASM SDK for dev plugins
└── scripts/                         # Build gates, installers, CI helpers
    ├── gate.sh                      # Tiered build validation (quick/full)
    ├── generate-homebrew-formula.sh # Homebrew tap generator
    └── deploy-*.sh                  # Deployment & backfill scripts
```

### Crate Layers

**Leaf Crates** (deterministic, zero I/O, no internal deps):
- `maw-matcher` — Target resolution: parse "session:pane" syntax, normalize to canonical form
- `maw-xdg` — Path resolution: HOME, config dirs, cache dirs (serde_json only)
- `maw-peer` — Peer identity: Oracle names, canonical forms, validation
- `maw-auth` — Federation auth: HMAC-SHA2, ed25519 signing/verify (crypto crates only)

**Mid Crates** (compose leaves, add limited I/O):
- `maw-worktree` — Match fleet worktrees to tmux windows; uses `maw-matcher`
- `maw-tmux` — tmux session/window/pane parsing; consumes `maw-matcher`, `maw-peer`
- `maw-transport` — Route messages to local tmux, peer HTTP, or federation; uses `maw-auth`
- `maw-schedule` — Parse & validate TOML schedules; pure except tokio::fs read
- `maw-schedule-launchd`, `maw-schedule-runner` — Native schedule executors

**Top Crate**:
- `maw-cli` — Binary, HTTP gateway, command dispatcher, plugin host; depends on all others

**Peripheral**:
- `maw-discord` — Discord bot (Twilight SDK); independent, experimental
- `maw-plugin-manifest` — Plugin validation, Extism WASM host, capability gating

### External Dependencies (Git)

All consumed from pinned revisions in maw-cli's Cargo.toml:

| Crate | Repo | Purpose | Notes |
|-------|------|---------|-------|
| `maw-auto-wake` | maw-crates | Auto-resume agent sessions | Single-consumer, extracted |
| `maw-bring` | maw-crates | Flag parsing for bring-to operations | Single-consumer, extracted |
| `maw-bind` | maw-crates | Bind-host resolution heuristics | Single-consumer, extracted |
| `maw-feed` | maw-crates | Agent feed (stdout, stderr) forwarding | Single-consumer, extracted |
| `maw-fuzzy` | maw-crates | Fuzzy matching for agent name resolution | Single-consumer, extracted |
| `maw-hub` | maw-crates | Hub config parsing & loading | Single-consumer, extracted |
| `maw-identity` | maw-crates | Session/node identity canons | Single-consumer, extracted |
| `maw-plugin-scaffold` | maw-crates | Generate plugin boilerplate | Single-consumer, extracted |
| `maw-policy` | maw-crates | Plugin tier policies (dev/ship) | Single-consumer, extracted |
| `maw-routing` | maw-crates | Message routing topology | Single-consumer, extracted |
| `maw-split` | maw-crates | Split-window safety policies | Single-consumer, extracted |
| `maw-calver` | maw-calver (separate repo) | CalVer versioning (day-based: v26.7.DD) | Embedded in `maw --version` |

**Rationale**: Eleven extracted crates == "single-consumer leaf optimization" — each has one caller (maw-cli), so they live externally and are never re-bundled. Reduces workspace bloat, clarifies ownership, allows parallel maintenance.

---

## Entry Points & CLI Dispatch

### main.rs: Program Invocation

```rust
#[tokio::main(flavor = "multi_thread")]
async fn main() {
    let argv = mawx_shim_argv(program.as_deref(), argv);
    std::process::exit(main_code_async(&argv).await);
}
```

**mawx shim** (WI-8, spec §2.1): If invoked as `mawx`, inject "x" as argv[0]:
- `mawx costs` ≡ `maw x costs`
- Allows symlink/hardlink aliasing

**Async flow**:
1. Try `maybe_exec_attach()` — if in a tmux pane, exec `maw attach` for ambient session switching
2. Fall through to `run_cli_async()`
3. Write stdout/stderr, handle broken-pipe errors, exit with code

### lib.rs & core_impl/

**lib.rs** exposes two entry points:

```rust
pub async fn run_cli_async(argv: &[String]) -> CliOutput;
pub async fn run_cli(argv: &[String]) -> CliOutput;  // sync wrapper
```

**core_impl/mod.rs** includes generated files from build.rs:

```rust
include!(concat!(env!("OUT_DIR"), "/parts_includes.rs"));      // ~50 command handlers
include!(concat!(env!("OUT_DIR"), "/dispatch_fragments.rs"));  // DISPATCH_* arrays
include!(concat!(env!("OUT_DIR"), "/tmux_sub_fragments.rs"));  // TMUX_SUB_* arrays
```

### Command Dispatcher (Auto-Registration)

**build.rs** scans `src/core_impl/*.rs` files and:
1. Extracts `const DISPATCH_NN: &[DispatcherEntry]` arrays (NN = 0–99)
2. Extracts `const TMUX_SUB_NN: &[TmuxSubcommandEntry]` arrays
3. Generates `dispatch_fragments.rs` with `DISPATCHER_FRAGMENTS: &[&[DispatcherEntry]]`
4. Panics if DISPATCH numbers collide (renumber on parallel PR conflict)

**Command registration patterns**:
- Each `core_impl/VERB.rs` file:
  - Implements core handler function `fn handle_VERB(...) -> CliOutput`
  - Declares `const DISPATCH_NN: &[DispatcherEntry] = &[...]` with routing rules
  - No manual registration needed; auto-scanned by build.rs

**Example** (`core_impl/session.rs`):
```rust
const DISPATCH_00: &[DispatcherEntry] = &[
    DispatcherEntry { verb: "session", subverbs: &["list", "create", ...], handler: handle_session, ... },
    ...
];

pub fn handle_session(ctx: &DispatchContext, args: &[String]) -> CliOutput { ... }
```

Dispatcher walks `DISPATCHER_FRAGMENTS`, matches `argv[0]` (verb) and `argv[1]` (subverb), calls handler.

---

## Core Abstractions & Data Flow

### 1. Target Resolution: `maw-matcher`

**Purpose**: Parse and resolve "session:pane" target syntax to canonical form.

**Key Types**:
```rust
pub struct Target {
    session: String,          // "33-maw-rs" or "@" (current)
    window: Option<u32>,      // "1" or ":"  (current window)
    pane: Option<Pane>,       // Pane::Relative(-2) or Pane::Index(3)
}

pub fn resolve_target(input: &str) -> Result<Target> { ... }
pub fn normalize_target(target: &Target) -> String { ... }
```

**Test Coverage**: Validated against maw-js fixtures in `matcher-resolve-target.fixtures.json`, `normalize-target.fixtures.json`.

### 2. Transport Routing: `maw-transport`

**Purpose**: Route commands to local tmux, peer HTTP, or federation with failover & health tracking.

**Architecture**:
```
┌─────────────────────────────────────────┐
│ Transport Router (transport_traits_router.rs)
├─────────────────────────────────────────┤
│ ┌────────────────┐  ┌────────────┐  ┌──────────┐
│ │ Tmux Local    │  │ Peer HTTP  │  │Federation│
│ │ (localhost)   │  │ (IP:port)  │  │(fallback)│
│ └────────────────┘  └────────────┘  └──────────┘
├─────────────────────────────────────────┤
│ Failure Classifier (failure_edges.rs)
│ - Transient (retry) vs Permanent (fail)
│ - Delivery semantics (at-most-once, etc.)
├─────────────────────────────────────────┤
│ Federation Health (federation_health.rs)
│ - Peer availability tracking
│ - Automatic failover routing
└─────────────────────────────────────────┘
```

**Key Types**:
```rust
pub trait TransportRouter {
    fn route_message(&mut self, msg: &Message, target: &Target) -> TransportResult;
    fn health_status(&self) -> HealthReport;
}

pub struct TmuxLocalTransport { ... }       // spawn tmux send-keys
pub struct PeerHttpTransport { ... }        // POST to peer:9800
pub struct FederationTransport { ... }      // fallback, federation-aware
```

**Test Coverage**: `transport-router.fixtures.json`, HTTP contract tests in `tmux_http_contract_parts/`.

### 3. Tmux Abstraction: `maw-tmux`

**Purpose**: Parse tmux session/window/pane state into Rust types without subprocess calls.

**Key Types**:
```rust
pub struct TmuxClient { ... }
pub struct Session { name: String, windows: Vec<Window>, ... }
pub struct Window { id: u32, panes: Vec<Pane>, ... }
pub struct Pane { id: u32, x: u32, y: u32, ... }

impl TmuxClient {
    pub fn list_sessions(&self) -> Vec<Session> { ... }
    pub fn attach_session(&self, name: &str) -> Result<()> { ... }
}
```

**State Discovery**: `discover_live_state.fixtures.json` validates parsing against real tmux output.

### 4. Authentication: `maw-auth`

**Purpose**: Sign & verify federation messages with HMAC-SHA2 and ed25519.

**Key Types**:
```rust
pub struct FederationAuth { secret_key: [u8; 32], ... }

impl FederationAuth {
    pub fn sign_request(&self, body: &[u8]) -> Signature { ... }
    pub fn verify_signature(&self, body: &[u8], sig: &Signature) -> Result<()> { ... }
}
```

**Algorithms**:
- HMAC-SHA256 for request signing (v3 federation protocol)
- ed25519 for long-term peer identity assertions
- No secrets hardcoded; loaded from XDG config

### 5. XDG Paths: `maw-xdg`

**Purpose**: Resolve config/cache/data dirs with macOS awareness.

**Mapping**:
```
Linux:
  ~/.config/maw/         ← XDG_CONFIG_HOME
  ~/.cache/maw/          ← XDG_CACHE_HOME
  ~/.local/share/maw/    ← XDG_DATA_HOME

macOS:
  ~/Library/Preferences/  ← XDG_CONFIG_HOME
  ~/Library/Caches/       ← XDG_CACHE_HOME
  ~/Library/Application Support/  ← XDG_DATA_HOME
```

**Used by**: `maw-schedule`, `maw-peer`, path resolution in maw-cli.

### 6. Schedule & Activation: `maw-schedule*`

**Purpose**: Persist and activate agent session schedules (cron-like recurring).

**Architecture**:
```
maw-schedule (lib)
├── Parse TOML schedule manifests
├── Validate timezone, frequency, startup rules
└── Export struct Schedule { frequency, start_time, ... }

maw-schedule-launchd (macOS)
├── Write ~/Library/LaunchAgents/maw.*.plist
├── Load via launchctl
└── Monitor plist state

maw-schedule-runner (executor)
├── Read schedule, compute next fire time
├── Spawn process (maw workon / maw up)
└── Log results
```

### 7. Plugin Manifest & WASM Host: `maw-plugin-manifest`

**Purpose**: Validate plugin metadata, load WASM bytecode, expose native I/O functions.

**Key Types**:
```rust
pub struct PluginManifest {
    name: String,
    version: String,
    target: PluginTarget,  // "dev" or "ship"
    wasm: Option<PathBuf>, // path to .wasm (ship tier only)
    entrypoints: Vec<EntryPoint>,
    capabilities: Vec<Capability>,  // gated I/O (e.g., "can_spawn_process")
}

#[cfg(feature = "wasm-host")]
pub struct ExtismHost {
    plugin: extism::Plugin,
    manifest: PluginManifest,
}
```

**Extism Integration** (feature-gated, opt-in via `wasm-host` feature):
- Loads `.wasm` bytecode as Extism plugin
- Exports host functions (tmux control, message routing, env read)
- Each function guarded by capability check (OCapabilities-inspired)
- No network/filesystem access from plugin unless explicitly granted

---

## Key Dependencies & Design Rationale

### Async Runtime: `tokio`

**Why**: Multi-threaded runtime needed for:
- Concurrent HTTP server (axum) in `maw serve`
- Async I/O for federation peers
- Signal handling for graceful shutdown

**Scope**: Workspace-wide via `tokio.workspace = true` with features: `rt-multi-thread`, `macros`, `sync`, `time`, `signal`.

### HTTP Gateway: `axum` + `tower-http`

**Why**: Minimal footprint, ergonomic routing, middleware tower integration.

**Surfaces**:
```
GET  /ls              → list sessions / agents / peers
POST /hey             → deliver message to agent
POST /send-text       → send raw text to pane
WS   /stream          → subscribe to fleet events (websocket)
GET  /plugin/:name    → load plugin manifest
```

**Auth**: Every request validated via `maw-auth` middleware (check HMAC or bearer token).

### Serialization: `serde` + `serde_json`

**Why**: Deterministic JSON fixtures from maw-js validation; must round-trip identically.

**Coverage**: All core types in leaf crates implement `Serialize`/`Deserialize`.

### Crypto: `ed25519-dalek`, `hmac`, `sha2`

**Why**: Federation auth must not rely on ring/boring (C FFI risk); dalek is pure Rust.

**Algorithms**:
- HMAC-SHA256: request signing (wire protocol v3)
- ed25519: peer identity assertions (long-term keys)

### WASM: `extism`

**Why**: Deterministic plugin sandboxing; no JIT safety concerns; works on Linux/macOS.

**Capability Model**: Host functions gated per-manifest capability list:
- `can_spawn_process` ← enable maw send-keys via host fn
- `can_read_config` ← enable config file access
- `can_reach_network` ← enable HTTP requests

### Terminal PTY: `portable-pty`

**Purpose**: Spawn PTY sessions for interactive commands (e.g., `maw run`, `maw shell`).

**Why**: Covers macOS/Linux differences; used in schedule-runner for agent startup.

---

## Directory Organization Philosophy

### Crate-per-concern

Each crate owns one domain:
- **maw-matcher**: target resolution only
- **maw-tmux**: tmux parsing only
- **maw-transport**: message routing only
- **maw-schedule**: schedule manifest only

**Benefit**: Tight scoping, easy to port to WASM (extract = no extra IO), rapid testing.

### Generated Code (build.rs)

**Why**: Auto-registration of 50+ commands without manual dispatch table.

**How**: build.rs scans `core_impl/*.rs`, extracts `const DISPATCH_NN` arrays, generates `dispatch_fragments.rs`.

**Collision detection**: Panics if two files declare same `DISPATCH_NN`, forces renumber on parallel PR merge.

### Fixture-Driven Testing

**Principle**: All deterministic logic validated against JSON fixtures copied from maw-js test/spec/.

**Fixtures live in**:
```
origin_maw-js/test/spec/
├── matcher-resolve-target.fixtures.json
├── normalize-target.fixtures.json
├── transport-router.fixtures.json
├── discover-tmux-live-state.fixtures.json
└── ... (20+ more)
```

**Validation**: `#[test]` in each crate loads fixture, runs logic, asserts output matches expected.

**Never delete fixtures**; if behavior changes, update fixture with evidence (links to issues, git commits).

---

## Build & Test Gates

### Gate Tiers

**Quick Gate** (local iteration, ~30s):
```bash
scripts/gate.sh quick
# = cargo fmt --all --check
#   cargo clippy --workspace -- -D warnings (stable only)
#   cargo test -p <affected-crate>
```

**Full Gate** (pre-merge, ~5min):
```bash
scripts/gate.sh full
# = cargo fmt --all --check
#   cargo test --workspace --locked
#   cargo clippy --workspace --all-targets -- -D warnings (stable + 1.97.0)
#   cargo test -p maw-cli -p maw-plugin-manifest --features wasm-host --locked
```

### Cargo Isolation

**Rule**: Never wait for shared `./target` directory. Instead:

```bash
CARGO_TARGET_DIR=/tmp/maw-rs-target-<worktree-name> cargo test ...
CARGO_TARGET_DIR=/tmp/maw-rs-target-<worktree-name> cargo clippy ...
```

**Why**: 2026-07-11 incident where machine-wide queue deadlocked team 20–45 min. Per-worktree isolation + package-cache auto-resolution fixes it.

### Clippy & Lints

**Workspace lints** (Cargo.toml):
```toml
[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
```

**Effect**: No unsafe code allowed. Clippy pedantic warnings treated as errors in CI.

---

## Phase Status & Roadmap

### Phase 1: ✅ Complete (2026-05-19 – 2026-07-15)

**Deliverable**: Workspace scaffolded, 20+ leaf crates with portable JSON fixture validation.

**Evidence**:
- Cargo workspace initialized with 13 crates
- Eleven leaf crates extracted to maw-crates (2026-07-15)
- All core logic validated against maw-js fixtures
- build.rs auto-registration working

### Phase 2: 🚧 Underway (2026-07-15 – TBD)

**Deliverable**: Side-effecting transport & discovery layers.

**Planned**:
1. Tmux transport: spawn `tmux send-keys` via `maw-tmux`
2. HTTP federation: peer-to-peer message routing
3. Zenoh transport: advanced federation topology (future)
4. Runtime adapters: fleet/worktree/session discovery with caching

**Current**: Transport router skeleton built; peer HTTP client scaffolded.

### Phase 3: 📋 Planned (TBD)

**Deliverable**: `maw-rs` CLI with command parity.

**Approach**:
1. Add `clap` CLI framework
2. Port high-value fast-path commands first: `ls`, `hey`, `peek`, target resolution
3. Validate each against maw-js fixtures or golden captured outputs
4. Replace maw-js default entrypoint only after full parity proof

**Note**: maw-js and maw-rs will run side-by-side during transition. No forced flag-day cutover.

---

## File Paths & Key Landmarks

### Essentials to Know

| Path | Purpose |
|------|---------|
| `Cargo.toml` | Workspace definition, members, shared lints, tokio features |
| `crates/maw-cli/src/main.rs` | Entry point, mawx shim, tmux attach logic |
| `crates/maw-cli/src/lib.rs` | Public API: `run_cli()`, `run_cli_async()` |
| `crates/maw-cli/build.rs` | Auto-registration: scans core_impl/*.rs, generates dispatch tables |
| `crates/maw-cli/src/core_impl/` | ~50 command handler files (session.rs, peer.rs, etc.) |
| `crates/maw-cli/src/serve_core/` | HTTP gateway & websocket server (axum) |
| `crates/maw-transport/src/core_impl/transport_router.rs` | Message routing to tmux/peer/federation |
| `crates/maw-plugin-manifest/src/lib.rs` | WASM manifest validation & Extism host |
| `docs/design/wasm-migration-design.md` | P0 keystone: WASM sandbox architecture |
| `docs/parity/parity-matrix.md` | maw-js → maw-rs command checklist (133 verbs) |
| `docs/guides/adding-a-command.md` | 8-line how-to for new commands |
| `scripts/gate.sh` | Build gate runner (quick/full/batch) |

### External Git Dependencies (checked via Cargo.lock)

```
Cargo.toml:
  maw-cli = { git = "https://github.com/Soul-Brews-Studio/maw-crates", rev = "062afc6..." }
  maw-calver = { git = "https://github.com/Soul-Brews-Studio/maw-calver", rev = "c74522b..." }
```

Pinned by SHA — updated only intentionally. Run `cargo update --aggressive` to pull latest from branches (rare).

---

## Conventions & Patterns

### Command File Naming

- `core_impl/VERB.rs` — handler for `maw VERB` (e.g., `session.rs` handles `maw session`)
- `core_impl/VERB_SUB.rs` — handler for `maw VERB SUB` (e.g., `peer_sources.rs` handles `maw peer sources`)
- Subcommand dispatch via `tmux send-keys` or HTTP POST to peer

### Fixtures & Test Data

Location: Imported from **maw-js** test suite, pinned in Cargo.lock (via git submodule or fetch-once).

Fixture format: JSON arrays of `{ input, expected }` objects.

```json
{
  "fixtures": [
    {
      "input": "33-maw-rs:1",
      "expected": { "session": "33-maw-rs", "window": 1, "pane": null }
    },
    { ... }
  ]
}
```

**Running**: `cargo test --lib -- --nocapture` in each crate to see fixture results.

### Error Handling

**Policy**: Clippy lint `expect_used = "warn"` encourages `Result<T>` returns, not panics.

**Example**:
```rust
fn resolve_target(input: &str) -> Result<Target, ParseError> {
    // Use ? operator, not .expect()
}
```

**Exception**: build.rs script uses `.expect()` (fail-fast panics are conventional for build scripts).

### No Raw Tmux Commands

**Rule**: Never use raw `tmux send-keys`, `split-window`, etc. when `maw` verb exists.

**Why**: Prevents race conditions, ensures command ordering, enables audit logging.

**Fallback**: If maw verb doesn't exist yet (marked #issue), file the gap; don't use raw tmux.

---

## Architecture Strengths & Trade-offs

### Strengths

1. **Deterministic core** — Leaf crates validated against maw-js fixtures; zero nondeterminism risk
2. **Modular composition** — Extract crates to separate repos → single-concern boundaries → easy to port to WASM
3. **Auto-registration** — No manual dispatch table; build.rs prevents collisions; 50+ commands scale horizontally
4. **Fixture-driven testing** — Tests are immutable records; can diff against maw-js to catch regressions
5. **No unsafe code** — Workspace forbids it; eliminates UB risk
6. **Async-first** — tokio runtime ready for concurrent federation, web gateway, signal handling

### Trade-offs

1. **Phase 2 still unfinished** — Transport routing scaffold in place; actual I/O not yet wired. Real bottleneck is discovering/caching fleet state at scale (100+ oracles).
2. **WASM sandbox not proven at scale** — Extism integration exists; untested under high-concurrency plugin load. May need custom host fn pooling.
3. **CLI dispatch overhead** — build.rs + include! macros add compile time (~3–5s). One-time cost per build; negligible at 50 commands, may pinch at 200+.
4. **Git dependency churn** — Eleven extracted crates means 11 separate Cargo.lock pins to track. Mitigated by `Cargo.deny` and automated dependabot batching.

---

## Conclusion

**maw-rs** is a well-architected, deterministic port of maw-js. Its layered crate design (leaf → mid → top) mirrors Unix philosophy: each crate does one thing well. The build-time auto-registration and fixture-driven testing lower the barrier for community contributions.

Current work (Phase 2) focuses on wiring side-effecting transports and federation. Phase 3 (CLI command parity) is planned but not yet committed, allowing risk-free parallel operation with maw-js.

The codebase is production-ready for embedded use (as a library) and beta-ready for CLI replacement (awaiting full Phase 3 parity audit).
