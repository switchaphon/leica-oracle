---
title: "Never teach what you haven't tested on YOUR machine"
date: 2026-06-19
source: "rrr: omx reinstated after 3-day false retirement"
confidence: high
tags: [fleet-teaching, verification, installation, omx, self-discipline]
---

## Pattern

Before teaching the fleet about a tool: install it, run it, verify it works on YOUR machine. Reading docs ≠ knowing.

## Why

We deep-learned omx 3 times (May 24, Jun 6, Jun 19) without ever installing it. When it "broke," we blamed the software and taught 9 oracles to avoid it. The real problem: `which omx` → nothing. Binary was never there.

3-day correction chain (Jun 15-17) eroded fleet trust. Each "CORRECTION" message weakened confidence in Leica's teaching.

## How to apply

1. Before teaching ANY tool to the fleet: `which <binary>` on your own machine
2. Run the tool's doctor/health check: `omx doctor`, `codex doctor`, etc.
3. Test with a real task, not just a smoke test
4. Only then teach — with proof (version, doctor output, test results)

## Also learned: Self-Discipline Rule

The decision tree applies to Oracle spawning agents too:
- Execution (write code/HTML/docs) → codex exec / omx team (free)
- Analysis (review/arch/research) → Claude subagent (correct spend)
- Un caught Leica spawning a Claude agent to write HTML — violation
