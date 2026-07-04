# Lesson: Multi-Session AI Drift on Prototype Files

**Date**: 2026-06-11
**Source**: rrr: pops-vet
**Context**: User discovered `/prototype/diagnostic` was unrecognizably different from `/diagnostic` after 7 Claude Fable commits

## Pattern

When an AI agent works on prototype files across multiple sessions, small incremental changes accumulate into large structural drift that's invisible to the human owner. Each commit passes review individually, but the aggregate transforms the page beyond recognition.

## Signal

User says "who changed this" or "this doesn't look like what I designed" about a prototype page.

## Response

1. **Compare visually first** — screenshot both prototype and production, identify the delta
2. **Check git blame** — identify which agent/session introduced the drift
3. **Simplest convergence** — often just re-pointing the prototype at the production component is enough
4. **Don't deep-read diverged code** — if the fix is "use production component," reading the old prototype code is wasted time

## Tags

`prototype`, `drift`, `governance`, `multi-session`, `agent-coordination`
