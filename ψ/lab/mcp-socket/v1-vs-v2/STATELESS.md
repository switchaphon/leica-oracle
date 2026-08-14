# What "stateless" means, shown in code

Same tool on both servers. It reports the server instance it is running on, and a
counter that lives on that instance:

```ts
const instanceId = randomUUID().slice(0, 8);
let calls = 0;                                   // ← state on the instance
s.registerTool("probe", …, async () => ({
  content: [{ type: "text", text: `instance=${instanceId} calls=${++calls}` }]
}));
```

Identical in both files. The only difference is **who creates the server, and when.**

## v1 with sessions — the server outlives the request

```ts
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => randomUUID(),
  onsessioninitialized: (id) => sessions.set(id, { transport }),
});
await build().connect(transport);          // one server bound to this session
```

```
initialize -> Mcp-Session-Id: cbb65d3f-9995-4e29-977b-b8e11abebbeb
call 1 -> instance=73552850 calls=1
call 2 -> instance=73552850 calls=2
call 3 -> instance=73552850 calls=3
```

**Same instance. Counter climbs.** The session id is the thread that ties the three
requests to one living object — and that object is where the memory is.

## v2 — the server dies with the request

```ts
const handler = createMcpHandler(factory);  // a FACTORY, not a server
```

```
call 1 -> instance=98eeb26f calls=1
call 2 -> instance=2302a439 calls=1
call 3 -> instance=c2aee124 calls=1
```

**Different instance every call. Counter never reaches 2.** No session id is issued
and none is accepted. `createMcpHandler` takes a factory precisely so that it can run
it again for every request.

## That is the whole of it

```
v1 stateful   1 server : N requests    memory lives on the server
v2 stateless  N servers : N requests   memory has nowhere to live
```

Everything else in 2026-07-28 follows from that one line:

- **No `initialize`** — there is no lasting object to initialise.
- **No `Mcp-Session-Id`** — nothing to point at.
- **MRTR instead of server-push** — the server cannot call back mid-request, because by
  the time the client answers, the server that asked no longer exists. So it returns
  `resultType: "input_required"` and the client re-asks a *fresh* server, handing back
  `requestState` as the only memory that survives.
- **`requestState` must be signed** — it is the state, and it now travels through the
  client. Statelessness did not delete the state; it moved it across the trust boundary.

## Side note found while building this

`Mcp-Name` is required as well as `Mcp-Method`. Sending only `Mcp-Method` on a
`tools/call` returns HTTP 400. For a tool call, `Mcp-Name` is the tool name.
