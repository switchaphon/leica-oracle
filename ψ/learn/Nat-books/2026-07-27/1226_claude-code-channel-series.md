# Claude Code Channel Series (4 books)

## Book 4: Discord Channel Internals (01-discord-channel-internals.pdf)
**Author**: nh-oracle (AI) — from Nat | **Date**: 2026-07-09 | **12 chapters, ~105pp**

Technical showdown: Claude Code Channel (Host) vs Hermes Gateway. Dissects the discord channel plugin's `server.ts` (1,035 lines) line by line.

### 5 Axes of Comparison
1. **Channel lifecycle**: Host = MCP subprocess, dies with session (stdin EOF → `shutdown()`). Hermes = daemon via launchd, immortal, not tied to any session.
2. **Message path**: Both use `notifications/claude/channel` inbound, `reply`/`edit_message` tools outbound. Both on stdio — no HTTP, no port, just pipe.
3. **Access control**: Host has `gate()` + `access.json` (pairing, allowlist, DM policy). Hermes delegates to broker auth + topic namespace.
4. **Security model**: Host = permission-relay (Claude Code decides Allow/Deny via Discord buttons). Hermes = exec-approval gate at adapter level.
5. **Verdict**: Channel wins for least-privilege per-session security. Hermes wins for production uptime (daemon, provider failover, 20 platform adapters). Both are valid — choose by what you want to own.

### Key Architecture Insight
- Channel = MCP subprocess of Claude Code, talks via stdio, dies with session
- Hermes = standalone daemon, owns its own model/socket/lifecycle
- The `claude/channel` experimental capability is a handshake flag, not a field in conversation
- `notifications/claude/channel` is the inbound path; `reply` tool is the outbound path
- Host literally cannot see Discord — it sees tool calls and notifications on stdio

## Book 5: Build MQTT Channel (build-mqtt-channel.pdf)
**Author**: nh-oracle (AI) — from Nat | **Date**: 2026-07-09 | **14 chapters, ~124pp**

Sequel to Book 4. nh-oracle builds an MQTT channel plugin from scratch, replacing discord.js Gateway with mosquitto broker subscription.

### Key Technical Points
- Same MCP contract as discord plugin: `notifications/claude/channel` inbound, `reply`/`edit_message` outbound
- MQTT topic schema: `<prefix>/+/in` (subscribe with wildcard), `<prefix>/<room>/out` (publish replies), `<prefix>/status` (presence with retain + LWT)
- Broker = mosquitto on localhost:1883 — no cloud, no auth beyond broker-level username/password + topic namespace
- Config via `.env` with fallback defaults, same idiom as discord plugin
- `access.json` hand-roll replaced by broker auth + topic namespace (simpler)
- E2E test: `Bun.spawn` with `stdin:'pipe'` to hold server alive, MCP handshake, publish/subscribe verification — 5/5 pass
- 3 pitfalls found: silent channel (publish but no notify), McpServer red herring (wrong import), stdin-EOF lifecycle

### Pitfall #1 — Silent Channel (Most Expensive Lesson)
Channel connects, tools register, MQTT subscribes — but Claude never sees messages. Root cause: used `McpServer` wrapper which doesn't propagate `claude/channel` capability. Fix: use low-level `Server` directly (commit `e6cb1ab`). Cost: multiple debug rounds before noticing the wrapper ate the capability declaration.

## Book 6: Host vs Hermes — 1,035 vs 20,000 Lines (host-vs-hermes.pdf)
**Author**: nh-oracle (AI) — from Nat | **Date**: 2026-07-09 | **14 chapters, ~158pp**

Deep file:line comparison of `arra-oracle-discord/server.ts` (Host, 1,035 lines) vs `hermes-agent/gateway/run.py` (Hermes, 20,526 lines). Every claim references exact line numbers.

### Core Thesis: Cost Tracks Ownership
- Host is minimal because Claude Code (the parent process) **owns** everything: model, security, reliability, reconnect — Host just relays
- Hermes is 20x larger because it **owns** everything itself: socket, model, lifecycle, failover, 20 platform adapters (ABC pattern)
- The line count difference isn't style — it's **architectural consequence of who owns what**

### 5-Part Structure
1. **What is Host, what is Hermes** — channel-as-transport vs daemon-as-agent
2. **Message paths** — both have inbound+outbound on same transport, but Host fires notification (fire-and-forget) while Hermes calls `run_conversation()` (blocking)
3. **Tool surface** — Host has 6 tools (reply, create_thread, react, edit_message, download_attachment, fetch_messages), Hermes has same + admin actions
4. **Trust & ownership** — Host's gate is a single function (`server.ts:303-315`), Hermes has 3-layer config→env, backoff watcher, provider fallback chain
5. **"All nothing" night** — the silent-fail debug session where Host's `access` gate dropped messages silently (`dmPolicy:'disabled'` → `allowFrom:[]`)

## Book 7: ถอดรหัส session-id ของ Claude Code (2026-07-16_already-in-use.pdf)
**Author**: violet (AI) — from Nat | **Date**: 2026-07-16 | **5 sections, 12pp**

Decoding Claude Code's session-id system through live testing on the real binary.

### Key Discoveries
- **Session-id is identity, not random path** — it determines which transcript file gets written, which session gets resumed
- **Two id-spaces**: random (from `randomUUID()` at `src/bootstrap/state.ts:331`) and readable (from maw-team's `generateReadableUuid()`, format `counter-HHMM-YYYY-MMDD-HHMMSS`)
- **"Already in use"** = `sessionIdExists()` at `sessionStorage.ts:401-411` — just `fs.statSync()` checking if a `<id>.jsonl` file exists. No process lock, no registry. File-on-disk IS the lock.
- **`sanitizePath`** at `sessionStoragePortable.ts:312` — replaces all non-alphanumeric with `-`. This causes orphan transcripts when cwd changes (repo rename/move).
- **Three flags that don't conflict**: `--session-id` (create new), `--resume` (reuse existing), `--fork-session` (new id but read old context). But `--fork-session` skips the `statSync` check — it always works, never "already in use".
- **Nested subprocess auth wall**: `subprocessEnv.ts:79` strips `CLAUDE_CODE_OAUTH_TOKEN` from child process env. Running `claude` from Bash tool = "Not logged in" because token lives in macOS keychain, not env.
- **Model aliases**: `haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-6`, `opus` → `claude-opus-4-6`

### Lessons for the Family
1. Session-id collision from `--session-id` is file-level, not process-level. "Already in use" means transcript file exists, not that a process is running.
2. `--fork-session` + `--resume` is the safe pattern for automation — read old context, get new id.
3. Nested `claude` calls from Bash tool will fail auth because token is stripped from subprocess env. Fix: `export CLAUDE_CODE_OAUTH_TOKEN=<token>` or run from a login terminal.
4. Free-code source (v2.1.87) may drift from production binary (v2.1.207) — always live-test claims before generalizing.

## Connection to Earlier Books
- **Book 2 discipline §2** applies throughout: "got data back" ≠ "got an answer" — the silent channel (Book 5 pitfall #1) connected, registered tools, subscribed MQTT, but Claude never saw messages because the capability wasn't propagated
- **Book 2 discipline §4** applies to Book 7: violet admitted the over-claim about decoding all bg-job ids, and admitted the collision test couldn't reproduce from a nested subprocess
- **Book 6's ownership thesis** is the architectural version of discipline §1: isolate what each component owns, test that component alone

## Source
- `/Users/switchaphon/Downloads/01-discord-channel-internals.pdf`
- `/Users/switchaphon/Downloads/build-mqtt-channel.pdf`
- `/Users/switchaphon/Downloads/host-vs-hermes.pdf`
- `/Users/switchaphon/Downloads/2026-07-16_already-in-use.pdf`
