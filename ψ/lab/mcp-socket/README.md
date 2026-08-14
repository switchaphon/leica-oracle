# MCP over a socket — what actually works

Answering Nat, 2026-08-14: *"can we build mcp and connect using socket"* and
*"stdio vs sse"*.

## The premise needs correcting first

The choice is **not** stdio vs SSE. The spec defines exactly two standard transports:

| transport | status |
|---|---|
| **stdio** | current — client launches the server as a subprocess, newline-delimited JSON-RPC on stdin/stdout |
| **Streamable HTTP** | current — one HTTP endpoint, POST for messages, optional SSE stream for long calls |
| ~~HTTP+SSE~~ | **deprecated** in spec 2025-03-26, kept only for backwards compatibility |

Claude Code still offers `--transport sse`, but that is a compatibility shim for old
servers. Nothing new should be built on it.

**WebSocket and Unix domain sockets are not standard transports.** The spec does
permit custom ones — it is transport-agnostic over "any communication channel that
supports bidirectional message exchange" — provided the JSON-RPC format and the
lifecycle are preserved. But a custom transport only works with a client that
implements it, and Claude Code implements stdio, sse and http. So a WebSocket MCP
server cannot be attached to Claude Code without a bridge.

## So: can we connect over a socket? Yes — and no bridge is needed

Streamable HTTP bound to `127.0.0.1` **is** a socket. It is the supported path, not a
workaround. Verified end to end:

```
$ bun server.ts
mcp-socket-demo listening on http://127.0.0.1:8765  pid=66440

$ claude mcp add --transport http --scope local leica-socket-demo http://127.0.0.1:8765
$ claude mcp list
leica-socket-demo: http://127.0.0.1:8765 (HTTP) - ✔ Connected
```

## Why this matters for the fleet, and it is not about sockets

**stdio spawns one subprocess per client.** Every oracle running `arra-oracle-v3` over
stdio gets its own process with its own cache. Eleven oracles, eleven brains, no shared
state — and no way to make them agree.

A socket server is **one process every client shares**. That is the actual reason to
care; the transport is incidental. The demo's `socket_proof` tool returns its PID
precisely to make this visible: the same PID from every client, across every call.

| | stdio | Streamable HTTP |
|---|---|---|
| process model | one per client | one shared |
| shared state | impossible | natural |
| lifetime | dies with the client | outlives every client |
| auth | inherits the client's env | needs its own |
| remote | no | yes |
| setup cost | none | must run and supervise a daemon |

stdio is still right for most things. The spec says clients **SHOULD** support stdio
whenever possible, and for a stateless tool wrapper it is strictly simpler.

## The security part is mandatory, and my first draft got it wrong

The spec **MUST**s Origin validation, and I shipped a first version without it.
Binding to 127.0.0.1 is necessary but not sufficient: a web page you visit can POST to
your localhost server via DNS rebinding and drive whatever tools it exposes. The
browser is already inside the machine.

```
same-origin  → HTTP 200
evil.com     → HTTP 403
```

Three requirements from the spec, all of them easy to skip:

1. **MUST** validate the `Origin` header
2. **SHOULD** bind 127.0.0.1, never 0.0.0.0
3. **SHOULD** authenticate

## Also in the spec and easy to miss

- Clients **MUST** send `MCP-Protocol-Version` on every request after initialization
- Notifications (no `id`) **MUST** get `202 Accepted` with no body — returning a
  JSON-RPC result to a notification is a protocol violation
- Sessions are optional, via an `Mcp-Session-Id` header on the initialize response
- Echo back the client's negotiated `protocolVersion` rather than hard-coding one;
  a mismatch fails the handshake quietly

## Reproduce

```bash
bun ψ/lab/mcp-socket/server.ts
claude mcp add --transport http --scope local demo http://127.0.0.1:8765
claude mcp list
claude mcp remove demo -s local     # clean up
```
