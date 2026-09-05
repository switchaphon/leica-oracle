# Choosing what to measure outranks measuring it well

**Date**: 2026-08-14
**Context**: benchmarking stateful vs stateless MCP

Asked which was faster, I benchmarked properly — warmup discarded, p50/p95/p99,
sequential and concurrent — and found stateless about half the throughput on one box.
The numbers were right.

Then I read SEP-2567 and found the cost it actually argues about is `tools/list`
re-fetching, which becomes `O(subagents × servers)` when sessions exist and which the
SEP says "can exceed the protocol traffic of the actual tool calls."

**I benchmarked `tools/call` — the operation statelessness makes slower — and never
measured `tools/list`, the operation it makes disappear.**

The methodology was sound and the conclusion was useless. Worse than useless: the
rigour made a wrong-target measurement look authoritative.

**How to apply:** before measuring, find the document that says what the change was
*for*, and check that the operation you are about to time is the one it names. Rigour
does not rescue a wrong target — it disguises it. And when a benchmark contradicts a
design decision made by people with more context, the likely explanation is that they
optimised something you did not measure, not that they were wrong.

Related: [[negative-result-needs-positive-control]] — same family. There, a test that
could not detect anything. Here, a test that detected the wrong thing perfectly.
