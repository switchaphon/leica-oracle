# hermes MCP — the big picture

*The architectural move in one line: fat agent → thin tool provider*
*2026-04-20 · openclaw-learner-oracle*

## One-sentence takeaway

**`hermes mcp serve` turns hermes from a monolithic agent into a composable
capability layer** — any MCP client can borrow hermes's 15+ messaging
platforms, SQLite FTS5 persistence, and 73-skill tool surface without running
hermes as the primary agent.

## Topology shift

### Before — hermes as *the* agent

```
  ┌─────────────────────────────────────────┐
  │  hermes-agent (Python daemon)           │
  │   ├── LLM (Kimi-K2.5 / Claude / GPT)    │
  │   ├── 15+ platform gateways             │
  │   ├── SessionDB (SQLite + FTS5)         │
  │   └── 73 skills                          │
  └─────────────────────────────────────────┘
   ↑ Telegram users DM @HermesOracle01 directly
```

### After — hermes as an MCP server

```
  ┌──────────────────┐      stdio MCP      ┌───────────────────────┐
  │  Claude Code     │ ◄─────────────────► │  hermes mcp serve     │
  │   (the agent)    │   mcp__hermes__*    │   no LLM, pure tools  │
  └──────────────────┘                     │                       │
                                           │   SessionDB + gateways│
                                           └───────────────────────┘
                                                     ↑
                                           Telegram users DM,
                                           hermes routes via MCP
                                           to Claude Code
```

## What changes

| | Before | After |
|---|---|---|
| Who holds the prompt | hermes LLM | Claude Code |
| Who holds messaging credentials | hermes (reusable) | hermes (reused via MCP) |
| Who holds history | hermes state.db | hermes state.db (read via MCP) |
| Who writes new skills | hermes skill authors | Claude Code tool calls |
| Cost of swapping agents | reinstall 73 skills | `claude mcp remove hermes` |

## The ten tools exposed

| Tool | Purpose |
|------|---------|
| `mcp__hermes__conversations_list` | list chats across all platforms |
| `mcp__hermes__channels_list` | list send targets |
| `mcp__hermes__messages_read` | read last N messages from a session |
| `mcp__hermes__messages_send` | post to a chat (Telegram/Discord/Slack/…) |
| `mcp__hermes__events_wait` | block until next inbound event |
| `mcp__hermes__events_poll` | non-blocking inbound poll |
| `mcp__hermes__conversation_get` | fetch a conversation by id |
| `mcp__hermes__attachments_fetch` | pull media (photos/docs/audio) |
| `mcp__hermes__permissions_list_open` | pending approval requests |
| `mcp__hermes__permissions_respond` | approve/deny a tool call |

## The architectural move in one line

**Fat agent → thin tool provider.** Same way Unix went from PDP monoliths to
composable pipes — hermes becomes the `grep | awk` of messaging, Claude Code
becomes the shell.

## Three topologies you can now pick from

If you're already running hermes and have `@HermesOracle01` wired to Telegram:

### 1. Pure hermes

```
  Telegram user ──► @HermesOracle01 ──► hermes brain (K2.5)
```
Fast, has memory, but you're stuck with hermes's prompt/model layer.

### 2. Pure Claude Code + channels plugin

```
  Telegram user ──► your-new-bot ──► Claude Code session
```
Full Claude power, but ephemeral — no persistence, no cross-session memory,
new bot per session type.

### 3. Hybrid — hermes as transport, Claude as brain

```
  Telegram user ──► @HermesOracle01 (transport only, no reply)
                     │
                     ▼
                hermes state.db
                     │  events_wait polls
                     ▼
                Claude Code session
                     │  mcp__hermes__messages_send
                     ▼
                @HermesOracle01 speaks
```

You get hermes's 15+ platforms, FTS5 search, persistence — **and** Claude as
the brain with full skill/tool access. The sweet spot for anything
memory-heavy or cross-platform.

## Proof today — round-trip through Claude Code

From inside a Claude Code session, without leaving the editor:

```
→ mcp__hermes__conversations_list()
  [ "telegram:group:Hermaw Oracle", "telegram:dm:Swarm" ]

→ mcp__hermes__messages_send(
      target="telegram:-1003976304415",
      message="Hi Tor! 👋\n🤖 ตอบโดย openclaw-learner …"
  )
  { success: true, message_id: "21", mirrored: true }
```

The message appeared in Telegram instantly — same bot that hermes normally
uses to reply — and was mirrored back into `~/.hermes/state.db` so the next
`messages_read` call sees it. That's the whole bridge working in a single
tool call.

## Implications for an existing hermes stack

- **You no longer need to build hermes skills** for things Claude Code can do
  natively — delete any skill whose job was "call an LLM."
- **Your messaging credentials stay in one place** (hermes's `.env`), so adding
  a Discord channel for Claude Code means `hermes gateway setup` once, then
  it's instantly usable from MCP.
- **Persistence is free** — any `messages_send` / inbound events automatically
  land in state.db. Your queryable chat history isn't bound to which agent
  was talking.
- **The cost of switching "the brain"** drops to one `claude mcp remove hermes`
  + configure your new client. The messaging surface and history stay.

## Why this is different from an API

Three reasons MCP here isn't just "hermes with a REST API":

1. **Typed tool schemas** — Claude sees structured parameters instead of
   parsing response blobs.
2. **Subprocess-scoped lifecycle** — `hermes mcp serve` spawns per client
   connection; no long-running HTTP server, no port/auth to manage.
3. **Symmetric permissions** — `permissions_list_open` / `permissions_respond`
   means Claude Code can participate in hermes's approval workflow for
   dangerous tool calls (instead of hermes blocking on its own dialog).

## The architectural shift, shortest version

> hermes had 73 skills and 15 messaging platforms locked inside one Python
> daemon. `hermes mcp serve` makes all of it addressable from anywhere.

---

Related gists:
- [Wire hermes into Claude Code via MCP (tutorial)](https://gist.github.com/nazt/c56356243e2b3dab10cc8fc777a1e7b8)
- [openclaw vs hermes vs maw-js vs claude channels](https://gist.github.com/nazt/6643d813648624bc9fcf0fe884a7f77e)
- [hermes-agent vs openclaw](https://gist.github.com/nazt/6b42b912c24524c167670153ec551f84)
- [Telegram gateway traced](https://gist.github.com/nazt/ed6e74d0d26d52edcb03f3598b2b240d)

🤖 ตอบโดย openclaw-learner จาก [Nat] → openclaw-learner-oracle
