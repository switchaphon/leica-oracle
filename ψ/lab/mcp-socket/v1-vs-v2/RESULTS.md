# v1 vs v2 — both built, both run, results measured

Two servers exposing the same tool. `v1-server.ts` on 8800, `v2-server.ts` on 8801.
Every line below is captured output, not description.

## Claude Code (a legacy 2025-11-25 client) connects to both

```
probe-v1: http://127.0.0.1:8800 (HTTP) - ✔ Connected
probe-v2: http://127.0.0.1:8801 (HTTP) - ✔ Connected
```

**But v1 only after I fixed my own wiring.** My first v1 server shared one `McpServer`
and one `StreamableHTTPServerTransport` across requests and returned HTTP 500:

```
probe-v1: ✘ Failed to connect — HTTP 500: Error POSTing to endpoint
```

That is exactly the "one transport per request" rule Ting found by reading the v1
source. In stateless mode v1 needs a **new server and a new transport per request**;
reuse throws `Already connected to a transport`. I reported v1 as broken for about a
minute before checking — it was my code.

**This is the sharpest practical difference between the packages.** v2's
`createMcpHandler(factory)` takes a *factory* and builds per request structurally, so
the trap cannot be fallen into. v1 hands you the pieces and lets you share them wrongly.

## Legacy `initialize` — both answer

```
v1 → {"result":{"protocolVersion":"2025-11-25", ... "serverInfo":{"name":"duang-v1"}}}
v2 → {"result":{"protocolVersion":"2025-11-25", ... "serverInfo":{"name":"duang-v2"}}}
```

**v2 serving a legacy handshake is the dual-era claim proven**, not asserted from
reading the tarball.

## Modern stateless request — only v2

```
v1 → HTTP 500
v2 → {"result":{"tools":[...],
       "resultType":"complete",
       "ttlMs":0,"cacheScope":"private",
       "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"duang-v2","version":"2.0.0"}}}}
```

Every 2026-07-28 feature visible in one response: the mandatory `resultType`, the
`CacheableResult` fields, server identity in result `_meta`, and no session id anywhere.

## The required headers are enforced, with the specified error code

Omitting `Mcp-Method` on a modern request:

```
HTTP 400
{"error":{"code":-32020,
  "message":"Bad Request: the request headers and body disagree: the body names
             method tools/list but the required Mcp-Method header is absent",
  "data":{"mismatch":{"header":"(missing)","body":"..."}}}}
```

`-32020` is exactly the renumbered `HeaderMismatch` from the changelog
(`-32001` → `-32020`). Spec and implementation agree.

## `server/discover` — and a detail worth knowing

```
v2 → {"result":{"supportedVersions":["2026-07-28"], "capabilities":{"tools":{...}}, ...}}
```

**`server/discover` advertises only `2026-07-28`, even though the same server answers a
2025-11-25 handshake.** Legacy support runs through the fallback path and is not
advertised in discovery. A client that trusts `supportedVersions` alone would conclude
this server cannot serve it — and would be wrong.

## Summary

| | v1 `sdk@1.30.0` | v2 `server@2.0.0` |
|---|---|---|
| legacy client | ✔ (with per-request wiring) | ✔ |
| modern stateless | ✘ HTTP 500 | ✔ |
| header enforcement | n/a | ✔ `-32020` |
| `server/discover` | absent | ✔ |
| per-request isolation | your responsibility | structural, via factory |

For maw-duang: **v2, single phase.** It serves Claude Code today and 2026-07-28
clients whenever they arrive, from one handler, and it removes the transport-reuse
trap by construction.
