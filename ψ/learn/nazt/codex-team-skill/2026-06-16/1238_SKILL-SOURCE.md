# /codex-team Skill Source (verbatim from Nat's gist)

> Source: https://gist.github.com/nazt/319bce17aa49ca6e9ac9529414e903ee
> Saved: 2026-06-16

```yaml
---
name: codex-team
description: "Codex team lifecycle — spawn, teardown, status, restart, scale. Wraps maw team commands with charter auto-discovery from ψ/teams/. Use when user says 'codex-team up', 'codex-team down', 'codex-team status', 'codex-team restart', 'codex-team scale', 'spawn team', 'kill team', 'team status', or wants to manage the codex coder fleet."
---
```

See gist for full content. Key sections:
- Charter discovery from `ψ/teams/*.yaml`
- Action: up (preflight → spawn → verify)
- Action: down (teardown → verify cleanup)
- Action: status (peek all + check PRs)
- Action: restart (down + up)
- Action: scale N (template for new members)
- 7 key rules
