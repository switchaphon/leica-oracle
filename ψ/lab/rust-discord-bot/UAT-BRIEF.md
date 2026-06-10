# UAT Brief — Rust Discord Bot

**From**: Leica (Lead Oracle, Claude Code)
**To**: Codex (Tester)
**Goal**: Find bugs BEFORE we submit to Oracle School. Add edge case tests, stress tests, and fix anything broken.

## Current State
- 10 tests pass, cargo build/test/clippy clean
- But tests only cover happy path — edge cases not tested

## UAT Test Cases to Add

### 1. Gateway Parsing Edge Cases
- Payload with missing `t` field (non-dispatch events like HEARTBEAT_ACK)
- Payload with `op: 11` (heartbeat ACK) — should not crash
- Payload with `d: null` for non-hello events
- Payload with extra unknown fields (Discord adds fields often) — should not fail
- Very large payload (>64KB content field)

### 2. Message Handler Edge Cases  
- Empty message content — should not crash
- Message with no mentions array (field missing entirely)
- Message where bot mentions itself (author.id == bot_user_id)
- Message with multiple mentions including bot
- Message from another bot (author.bot = true) — should still respond if mentioned

### 3. Chunking Stress Tests
- Exactly 2000 chars — should be 1 chunk, not 2
- 2001 chars — should be 2 chunks  
- Empty string — should return 1 empty chunk (current behavior, verify)
- All emoji (4-byte chars): "🔥".repeat(2001) — must split on char boundary
- Mixed Thai + emoji + ASCII
- Single char that is > 2000 bytes but 1 char (impossible in practice, but test the logic)

### 4. REST Module
- Verify URL construction with special characters in channel_id
- Verify Authorization header format is exactly "Bot {token}"

### 5. Error Module  
- Verify all error variants produce meaningful Display output
- Verify From<tungstenite::Error> and From<ureq::Error> work correctly
- Test DiscordError::Gateway with empty string

### 6. Types Deserialization
- MessageData with `mentions: []` (empty array)
- MessageData without `mentions` field at all (should default to empty via serde)
- Author with `bot: false` vs missing `bot` field (should default false)
- GatewayPayload with `s: null` (no sequence yet — initial connect)

## Rules
- Add tests as `#[cfg(test)]` inline in each module
- No `unwrap()` — use `?` with Result return types
- Every test must have a descriptive name
- Run `cargo test` after each batch of tests
- Run `cargo clippy -- -D clippy::unwrap_used` at the end
- If any test reveals a bug in the implementation, FIX the bug too

## When Done
Report:
1. How many new tests added
2. Any bugs found and fixed
3. Final `cargo test` output
4. Final `cargo clippy` output
