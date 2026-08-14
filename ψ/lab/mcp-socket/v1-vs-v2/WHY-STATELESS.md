# Which is faster, and why they changed it anyway

## Measured, same machine, same tool

Sequential, 300 calls each after 40 warmup:

```
                  mean      p50      p95      p99   handshake
v1 stateful      0.195    0.163    0.344    1.149   19.10 ms once
v2 stateless     0.290    0.209    0.928    1.834   none
```

Concurrent, 512 calls at concurrency 64:

```
v1 stateful    52 ms  →  9895 req/s
v2 stateless  103 ms  →  4979 req/s
```

**Stateless is slower. About half the throughput on one box, and ~48% more latency
per call.** That cost is real and worth stating plainly, because it is the opposite of
what "the new spec" usually implies.

Break-even on the handshake: stateful's 19 ms setup pays for itself after roughly
**202 calls**. Below that, stateless is cheaper overall; above it, stateful wins.

## So why change it?

**Not for speed.** The official rationale (SEP-2567 / SEP-2575) is that the session
never meant anything reliable:

> *"After more than a year in the spec, sessions have not converged on a consistent
> meaning across clients: some scope them per tool call, some per application launch,
> some per page load, and almost none resume them. A server author cannot predict what
> scope or lifetime a session will have when their server is connected to an arbitrary
> client, which has made the session unreliable as a container for application state."*

That is a **semantic** failure, not a performance one. The abstraction existed, clients
implemented it differently, and so servers could not build on it. A container whose
lifetime you cannot predict is not a container.

Second reason, and a subtle one: **sessions block list caching.** A client cannot cache
`tools/list` across a session boundary unless it knows the server does not mutate lists
per session — and it cannot know that in advance. Removing sessions is what makes
`ttlMs` and `cacheScope` meaningful, which is why those fields appear in the same
revision.

Third: any request can land on any instance. Sticky routing and shared session stores
stop being required *at the protocol layer*.

## The arithmetic that resolves the apparent contradiction

```
1 stateful box     9895 req/s
1 stateless box    4979 req/s
2 stateless boxes  ~9958 req/s   ← parity
3 stateless boxes  ~14937 req/s  ← past anything one stateful box can reach
```

Stateful is faster **per box**. Stateless is faster **per rack**, because adding boxes
is trivial.

And the moment stateful has to scale past one box it must externalise the session —
sticky routing, or Redis. That external lookup is a network hop on *every* request,
which costs far more than the 0.094 ms stateless pays to construct an object locally.

**Stateful wins the benchmark I could run. Stateless wins the one that actually
matters, and I cannot run it on a laptop — so I am reporting the number that makes my
case look worse, and saying why it is the wrong number to decide on.**

## Reproduce

```bash
bun v1-stateful.ts &   # 8810
bun v2-server.ts &     # 8801
bun bench.ts           # sequential
bun bench2.ts          # concurrent
```
