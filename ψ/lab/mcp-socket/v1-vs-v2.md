# `@modelcontextprotocol/sdk` v1 vs `@modelcontextprotocol/server` v2

Read from the published tarballs on 2026-08-14, not from docs. Both pulled from
registry.npmjs.org and unpacked.

| | v1 `sdk@1.30.0` | v2 `server@2.0.0` |
|---|---|---|
| protocol versions shipped | `2025-11-25` and earlier | **`2025-11-25` *and* `2026-07-28`** |
| dependencies | **17** — express, hono, cors, jose, ajv, eventsource, pkce… | **2** — `@modelcontextprotocol/core`, `zod` |
| files in package | 728 | 87 |
| entry shape | `new McpServer()` + a long-lived transport | `createMcpHandler(factory, options?)` |
| server lifetime | one server, many requests | **factory builds a new server per request** |
| state | session (`Mcp-Session-Id`) | stateless by default; carry state in handles |
| transports | stdio, SSE *(deprecated)*, StreamableHTTP | stdio, `PerRequestHTTPServerTransport` |
| WebSocket | already removed | never present |

## The finding that matters: v2 does dual-era for you

I had told Tonk that anyone writing a 2026-07-28 server "must hand-write dual-era,"
because Claude Code is a legacy client and Legacy+Modern is a failing row in the
compatibility matrix. That was right about the requirement and **wrong about the
effort** — v2 ships era routing as API:

```ts
type ProtocolEra = 'legacy' | 'modern'

createMcpHandler(factory: McpServerFactory, options?: CreateMcpHandlerOptions): McpHttpHandler
legacyStatelessFallback(factory: McpServerFactory, onerror?): LegacyHttpHandler
classifyInboundRequest(request: InboundHttpRequest): InboundClassificationOutcome
isLegacyRequest(...)   isInitializeRequest(...)   isInitializedNotification(...)
```

plus `InboundLegacyRoute`, `InboundModernRoute`, `InboundLegacyRouteReason`,
`InboundValidationRung`, `InboundLadderRejection`.

And the receipt that settles it — both version strings are in the shipped bundle:

```
dist/index.mjs        "2025-11-25"
dist/mcp-*.mjs        "2026-07-28"
dist/src-*.mjs        "2025-11-25"  "2026-07-28"
```

So v2 is not "the 2026-07-28 package." **It is the dual-era package**, which is
exactly the thing the compatibility matrix says you need.

## What v2 adds that v1 has no concept of

- **MRTR**: `InputRequiredResult`, `inputRequired()`, `inputResponse()`,
  `isInputRequiredResult`, `InputRequests`/`InputResponses`, `RequestStateAccessor`
- **`server/discover`**: `DiscoverRequest`, `DiscoverResult`
- **`subscriptions/listen`**: `SubscriptionsListenRequest`/`Result`,
  `SubscriptionFilter`, `SubscriptionsAcknowledgedNotification`
- **The `_meta` keys as constants**: `PROTOCOL_VERSION_META_KEY`,
  `CLIENT_INFO_META_KEY`, `CLIENT_CAPABILITIES_META_KEY`, `SERVER_INFO_META_KEY`,
  `LOG_LEVEL_META_KEY`, `SUBSCRIPTION_ID_META_KEY`, `RELATED_TASK_META_KEY`
- **OpenTelemetry**: `TRACEPARENT_META_KEY`, `TRACESTATE_META_KEY`, `BAGGAGE_META_KEY`
- **Caching**: `CacheHint`, `CacheScope` (the `ttlMs`/`cacheScope` fields)
- **New errors**: `UnsupportedProtocolVersionError`,
  `MissingRequiredClientCapabilityError`, `UrlElicitationRequiredError`

## Practical read

The 17→2 dependency drop is the shape of the whole release. v1 bundled a web
framework; v2 assumes you bring your own and hands you a request handler. That is
what makes it work on Cloudflare Workers — there is a `validators/cf-worker` export.

For maw-duang specifically: the tools are pure functions, so none of MRTR, tasks,
subscriptions or handles is needed. `createMcpHandler` + register tools + bind
127.0.0.1 is the whole job, and legacy clients keep working for free.
