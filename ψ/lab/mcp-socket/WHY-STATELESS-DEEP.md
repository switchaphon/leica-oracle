# Why MCP went stateless — from SEP-2567 (Final), not from commentary

I benchmarked stateless as **2× slower per box**. So the interesting question is why
they did it anyway. The answer is in SEP-2567, and it is not a performance argument.

## The core finding: the session never meant anything

> *"After more than a year in the spec, sessions have not converged on a consistent
> meaning across clients: some scope them per tool call, some per application launch,
> some per page load, and almost none resume them."*

With citations, not assertion:

| client behaviour | evidence |
|---|---|
| ChatGPT opens a **fresh session per tool call** | playwright-mcp#1045, Sep 2025 |
| Claude.ai did the same until recently | same issue |
| "fresh MCP session each invocation" | OpenAI community, Nov 2025 |
| desktop/IDE: one per app launch, kept for process life | — |
| web: one per page load | — |
| TS SDK cannot rehydrate a session on another node | typescript-sdk#1658, Mar 2026 |

So a server author could not know what a session *was*. A Playwright server tying a
browser to "the session" cannot tell whether that means one user turn, one agent
process, or one long chat — and the host decides, not the server.

> *"Servers that appear to be using session state successfully are usually stdio
> servers relying on process lifetime, which is a property of the transport rather
> than the protocol."*

That sentence is the whole diagnosis. Session state mostly worked by accident, on
stdio, for reasons that had nothing to do with sessions.

## The performance argument is real — but it is not about tool calls

This is where my own benchmark measured the wrong thing.

Because `tools/list` may vary per session, a client **cannot cache it across session
boundaries**. For an orchestrator spawning subagents that is
`O(subagents × servers)` list calls — every subagent, every server, every time:

> *"For an orchestrator spawning many short-lived subagents, this overhead can exceed
> the protocol traffic of the actual tool calls."*

Removing sessions makes it `O(servers)`: fetch once, every subagent inherits the cache.

**I benchmarked `tools/call` — the operation stateless makes slower — and never
measured `tools/list`, the operation it makes disappear.** My numbers are correct and
answer the wrong question.

This is also why `ttlMs` and `cacheScope` (SEP-2549) ship in the same revision: caching
is only sound once lists cannot vary per session.

## Cardinality: one session gives exactly one of everything

An orchestrator spawns subagents to research products. They should share **one cart**
but each needs **its own browser**:

| session model | cart (want shared) | browser (want isolated) |
|---|:---:|:---:|
| subagents share parent's | ✓ | ✗ clobbers |
| subagents get their own | ✗ | ✓ |

**No session boundary satisfies both.** With handles the orchestrator calls
`create_basket()` once and each subagent calls `create_browser()` — the model decides
what is shared per piece of state, instead of one scope being imposed on everything.

Related: session state has no name, so it is invisible outside the chat that made it.
A `basket_id` can be handed to another agent, resumed tomorrow, or shared with a
colleague. A session cannot.

## Why remove it rather than make it optional

> *"The `O(subagents × servers)` cost is caused by sessions being **possible**, not by
> sessions being **used**."*

A client cannot cache lists unless it knows no connected server opts into session
scoping — and it cannot know that in advance. Optional sessions keep the entire cost.
Also: *"the primitive influences server design"*, and every concept must be
implemented, documented and learned.

For the same reason the rollout is a **clean break with no deprecation window** — a
version where clients supported both modes would forfeit the caching benefit outright.

## How much actually breaks: they counted

An automated survey of a **1000-repo random sample** of open-source MCP servers:

```
90.0%  no application-level reference to session ID   → nothing to do
 3.5%  Map<sessionId, Transport> boilerplate          → removed by sessionless transport
 2.8%  transport setup only, never read               → delete one constructor option
 2.5%  session-keyed application state                → migrate to handles
 0.7%  proxy/gateway sticky routing                   → needs a designed replacement
 0.5%  auth binding (PKCE, JWT claims)                → server-generated nonce
```

**Only ~3.7% genuinely break.** They removed a load-bearing-looking abstraction after
measuring that it was not load-bearing.

## Resumption gets better, not worse

Handles appear in tool results, so they are **part of the chat transcript**. Any client
that persists chats persists the handles for free — reopen the conversation on another
device and the handle is back in front of the model with no resumption machinery.
Session IDs required the client to persist and resend `Mcp-Session-Id` out of band,
which almost none do.

## And sessions were already a security problem

> The Python SDK's stateful session manager *"routes by `Mcp-Session-Id` alone without
> verifying that the authenticated identity on the request matches the one that created
> the session, so a leaked session ID allows hijack by any other authenticated
> principal."* — python-sdk#2100

Sessions were already capability-bearing. Handles do not introduce that class of bug;
they make it visible. The rule is the same either way: validate
`(handle, auth_context)` on **every** call. Possession is not authorization.

## Summary

They did not switch to stateless because it is faster. **It is slower per box, and I
measured that.** They switched because:

1. The session had no definable lifetime, so servers could not design against it.
2. Its mere *possibility* blocked list caching for everyone, used or not.
3. It forced exactly one scope per connection when real work needs several.
4. It was unaddressable, unresumable, and quietly capability-bearing.
5. They counted, and 96% of servers did not use it.

The 2× throughput cost buys an abstraction that can be reasoned about. That is a
trade, not a win — and the SEP is honest enough to present it as one.
