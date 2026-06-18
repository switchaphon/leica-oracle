---
title: "Test before teaching fleet — pilot 1 oracle, verify, then deploy to 9"
date: 2026-06-17
source: "rrr: 3-day correction chain on codex deployment"
confidence: high
tags: [fleet-teaching, verification, pilot, correction-chain]
---

## Pattern

New knowledge → pilot with 1 oracle → verify it works in practice → deploy to fleet

## Why

Teaching 9 oracles simultaneously means correcting 9 oracles simultaneously when wrong. Over 3 days:
- Day 1: engine:codex + .maw/teams/ + send-keys → all wrong
- Day 2: engine:omx + ψ/teams/ + maw hey → omx broken
- Day 3: codex exec direct → finally right

Each correction required 4 rounds of messages to 9 oracles. Trust erodes with every "CORRECTION" message.

## How to apply

1. Pilot: teach 1 oracle (preferably rpro-ent — it verifies independently)
2. Verify: wait for oracle to try it + report results
3. Fix: correct based on real-world feedback
4. Deploy: teach remaining 8 oracles the verified version
5. Label: if still experimental, say "this is experimental" not "this is the way"

## Also learned

- Teach CONCEPTS before COMMANDS — "two separate binaries" matters more than "codex exec -s workspace-write"
- rpro-ent's verify pattern (which/doctor/deprecate/runbook/commit) should be the standard for every oracle receiving new knowledge
