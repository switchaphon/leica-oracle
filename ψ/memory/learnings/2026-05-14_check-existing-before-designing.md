# Check Existing Code Before Any Domain Analysis

**Date**: 2026-05-14
**Source**: Lab Order data model session — spent 90 min re-deriving what mock-tests.ts already encoded
**Severity**: High — wasted ~60 min of Un's time

## The Pattern

When asked to analyze or design something for a feature, always check:
1. `find` the prototype directory for existing implementations (types, mock data, components)
2. `grep` brain files (ψ/inbox/handoff/, ψ/memory/retrospectives/) for the feature name
3. Read existing code FIRST, then frame the new analysis as "bridging to production" not "designing from scratch"

## Why

Un's team had already built the full Lab Order prototype across 6 sessions (05-02 to 05-11): 12 tests, 5 panels, 3 external providers, price multipliers, unavailability matrix, 5-state lifecycle, result viewer. All in `mock-tests.ts` and `types.ts`. The data model I created IS useful for backend but the domain decisions were already made.

## How to Apply

Before ANY feature analysis:
```bash
find ~/_POPs_/pops/app/vet/src/app/prototype -name "*lab*" -o -name "*diagnostic*" | head -20
grep -rl "lab" ψ/inbox/handoff/ ψ/memory/retrospectives/ | head -10
```

If results exist, read them first and say: "I see we already have X — here's what's new in this analysis."
