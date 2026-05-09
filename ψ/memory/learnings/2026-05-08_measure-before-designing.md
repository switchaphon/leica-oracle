---
source: "rrr: leica-oracle"
date: 2026-05-08
tags: [data-driven, skill-audit, infrastructure, measurement]
confidence: high
---

# Measure Before Designing

When planning infrastructure changes, get usage data first. Don't guess which skills/tools/features are needed — measure which ones are actually used.

## The Case

- 58 skills installed globally for all oracles
- Assumed most were needed — designed distribution based on role logic
- Then measured: only 18 ever used (69% dead weight)
- The data made the distribution design trivial — no guessing needed

## The Corollary: "Works Here" ≠ "Works Everywhere"

maw hey works perfectly at the terminal. But "works at the terminal" ≠ "works from a phone" or "works from a different machine." Always ask: what contexts does the user operate in beyond the current one?

## How to Apply

1. Before redesigning infrastructure: measure current usage first (`grep` session logs, check analytics)
2. Before dismissing alternatives: list all user contexts (mobile, remote, multi-machine)
3. Let data drive tier assignments, not role assumptions
