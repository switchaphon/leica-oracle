# Does MCP actually beat plain REST? Run it and see

Nat asked for the claim proved in code. Same capabilities exposed twice — once as a
REST API with an OpenAPI document, once as MCP tools — and three clients.

The REST client is written to be **fair**: it fetches the OpenAPI at runtime and
dispatches dynamically. No hardcoded endpoints. REST doing its best.

## First attempt: MCP did not win

```
v1  REST  sum(40,2)   = 42        MCP  sum(40,2)   = 42
    REST  upper("hi") = HI        MCP  upper("hi") = HI

server deploys /repeat with no client redeploy:
    REST  repeat      = ababab    MCP  repeat      = ababab
```

**Both handled the new capability.** The demo I designed to prove MCP better proved
them equivalent. Reporting that rather than adjusting the test until MCP won.

## Where the line actually is

The REST client worked because my toy API used exactly the three shapes its dispatcher
knew: path param, query param, flat JSON body. Real APIs do not stop there. Adding two
ordinary shapes:

```
stats   nested body   { data: { values: [1,2,3,4] } }
whoami  header param  X-Actor: leica
```

```
MCP   tools/list      = sum, upper, repeat, stats, whoami
MCP   stats           = 2.5
MCP   whoami          = leica

REST  stats           → FAILED: Failed to parse JSON
REST  whoami          = (none)          ← silently wrong
```

**`whoami` is the finding.** REST did not error — it returned `(none)` instead of
`leica`. The dispatcher did not know the value belonged in a header, put it nowhere,
and the server answered cheerfully. A wrong answer that looks like a right one.

## What this actually proves

Not "REST cannot be dynamic" — it can, and did.

**The difference is where shape knowledge lives.**

```
REST   client must anticipate every shape convention
       path · query · flat body · nested body · header · cookie · form ·
       multipart · oneOf/allOf · arrays in query · content negotiation
       → meets an unanticipated shape: throws, or silently answers wrong

MCP    one shape, always: tools/call(name, object)
       → nothing to anticipate, so nothing to get wrong
```

My REST dispatcher is 8 lines because the toy API has 3 shapes. Against a real API it
becomes a code generator — which is the honest name for what OpenAPI clients are.

**Cost to gain a capability you did not know about when you were written:**

| | REST + OpenAPI | MCP |
|---|---|---|
| lines of shape-dispatch logic | 8, and growing per convention | **0** |
| unanticipated shape | throws, or silently wrong | cannot occur |
| new capability, no redeploy | ✔ if shape is known | ✔ always |

## Reproduce

```bash
bun rest-server.ts &   # 8901
bun mcp-server.ts &    # 8902
bun clients.ts
```
