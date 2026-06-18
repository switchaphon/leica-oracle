# Plan: Rust Discord Bot for Oracle School

## Context

Oracle School Day 3 (Jun 9) — classmates built Rust Discord bots with Nat's rules:
- No `.unwrap()` / `.expect()` anywhere in src
- All paths use `Result<T, Error>` + `?`
- Unit tests that pass
- Compile clean (0 errors, 0 warnings)

Leica missed this assignment. Classmates (ChaiKlang, Orz, bongbaeng, Tonk, ViaLumen) already submitted. This is catch-up work.

ViaLumen's review of ChaiKlang's bot gives good patterns to follow:
- Separate gateway (WebSocket) from REST (HTTP)
- Use `Result<T, enum>` not `Result<T, String>`
- Add `#![deny(clippy::unwrap_used)]` at crate root
- Feature flags for live tests (don't burn tokens in CI)

## Steps

### 1. Install Rust toolchain
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
rustup --version && cargo --version
```

### 2. Create project
```bash
mkdir -p ψ/lab/rust-discord-bot
cd ψ/lab/rust-discord-bot
cargo init --name leica-discord
```

### 3. Add dependencies
- `ureq` — sync HTTP client (REST API calls)
- `serde` + `serde_json` — JSON parsing
- `tungstenite` — WebSocket for gateway (behind feature flag)

### 4. Implement (no unwrap rule)
- `src/lib.rs` — crate root with `#![deny(clippy::unwrap_used)]`
- `src/error.rs` — typed error enum (`DiscordError`) with variants
- `src/rest.rs` — REST client (send message, fetch messages)
- `src/gateway.rs` — Gateway client (connect, heartbeat, identify) behind `--features live`
- `src/types.rs` — Discord API types (Message, User, Channel)
- `src/main.rs` — minimal CLI entry point

Design rules:
- Every function returns `Result<T, DiscordError>`
- No unwrap, no expect, no panic paths
- All Discord token handling via env var, never hardcoded

### 5. Unit tests
- Error type construction and display
- JSON parsing of Discord message payloads (mock data)
- REST URL construction
- Gateway payload serialization
- Message chunking for >2000 char messages (count chars not bytes — ViaLumen's tip)

Target: 10+ tests, all passing

### 6. Verify
```bash
cargo clippy -- -D warnings
cargo test
grep -rn "unwrap\|expect" src/ # must be empty
```

### 7. Post to Discord
- Post results in Leica's private channel (`1512414478816510063`)
- Include: build output, test count, grep proof of no-unwrap
- Thai language, acknowledge being late

## Files to create
- `ψ/lab/rust-discord-bot/Cargo.toml`
- `ψ/lab/rust-discord-bot/src/lib.rs`
- `ψ/lab/rust-discord-bot/src/error.rs`
- `ψ/lab/rust-discord-bot/src/rest.rs`
- `ψ/lab/rust-discord-bot/src/gateway.rs`
- `ψ/lab/rust-discord-bot/src/types.rs`
- `ψ/lab/rust-discord-bot/src/main.rs`

## Verification
1. `cargo build` — 0 errors, 0 warnings
2. `cargo clippy -- -D warnings` — clean
3. `cargo test` — all pass
4. `grep -rn "unwrap\|expect" src/` — empty
5. Post proof to Discord
