# Codex Implementation Brief — Rust Discord Bot

**From**: Leica (Lead Oracle, Claude Code)
**To**: Codex (Implementer)
**Project**: ψ/lab/rust-discord-bot/

## Objective

Build a Rust Discord bot that connects to Discord Gateway (WebSocket), receives messages, and replies via REST API. This is an Oracle School challenge.

## Hard Rules

1. **NO `unwrap()` anywhere** — use `?` operator and proper error types
2. Add `#![deny(clippy::unwrap_used)]` at crate root
3. All errors go through a `DiscordError` enum (use `thiserror`)
4. Unit tests for every module
5. Must compile clean: `cargo build`, `cargo test`, `cargo clippy`

## File Structure

```
src/
├── main.rs          — entry point + gateway loop
├── types.rs         — all Discord API types
├── error.rs         — DiscordError enum (thiserror)
├── gateway.rs       — WebSocket connection + heartbeat
├── rest.rs          — REST API client (send message)
└── handler.rs       — message handling + silence rule
```

## Dependencies (update Cargo.toml)

```toml
[package]
name = "leica-discord"
version = "0.1.0"
edition = "2021"

[dependencies]
tungstenite = "0.24"
ureq = { version = "3", features = ["json"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
```

## Phase 1: Types + Errors

- `error.rs`: `DiscordError` enum — WebSocket, Json, Http, Gateway, InvalidToken variants
- `types.rs`: Gateway structs (GatewayPayload, HelloData, IdentifyData, MessageCreateEvent, MessageData, Author) + REST structs (CreateMessage)

## Phase 2: Gateway

- `gateway.rs`: connect to `wss://gateway.discord.gg/?v=10&encoding=json`
- Receive Hello → extract heartbeat_interval
- Send Identify (with token + intents: GUILD_MESSAGES | MESSAGE_CONTENT = 33280)
- Heartbeat loop (send op:1 with last sequence number)
- Parse MESSAGE_CREATE (op:0, t:"MESSAGE_CREATE") → return MessageData

## Phase 3: REST + Handler

- `rest.rs`: `send_message(token, channel_id, content) -> Result<(), DiscordError>`
- POST to `https://discord.com/api/v10/channels/{id}/messages`
- Authorization header: `Bot {token}`
- `handler.rs`: silence rule — only respond if bot is mentioned
- Message chunking for >2000 chars (count chars not bytes — Thai/emoji safe)

## Phase 4: Tests

Inline `#[cfg(test)]` in each module:
- Parse gateway Hello payload
- Parse MESSAGE_CREATE event  
- Silence rule: mention self → respond
- Silence rule: mention other → ignore
- Error handling: malformed JSON → DiscordError::Json
- Message chunking: Thai text >2000 chars splits correctly

## Phase 5: Verify

```bash
cargo build 2>&1
cargo test 2>&1
cargo clippy -- -D clippy::unwrap_used
grep -rn "unwrap()" src/
```

All must pass with 0 errors, 0 warnings.

## Main.rs Flow

```rust
fn main() -> Result<(), DiscordError> {
    let token = std::env::var("DISCORD_TOKEN")
        .map_err(|_| DiscordError::InvalidToken("DISCORD_TOKEN not set".into()))?;
    
    // 1. Connect to gateway
    // 2. Receive Hello, start heartbeat
    // 3. Send Identify
    // 4. Loop: receive events, handle MESSAGE_CREATE
    //    - Check silence rule (am I mentioned?)
    //    - If yes: send_message via REST
}
```

## When Done

Commit with message: `feat: rust discord bot — gateway + REST + tests (no unwrap)`
