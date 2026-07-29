---
title: Silent credential override — file beats env var without warning
date: 2026-07-28
source: "rrr --deep: leica-oracle"
concepts: [auth, credential-precedence, silent-failure, debugging, config-override]
---

## Pattern: Silent Config-Over-Env Override

When a config file and an environment variable both supply a credential, the file usually wins —
and nothing tells you. Every diagnostic passes: env var set, direnv loaded, pass decrypting,
token strings distinct. But auth silently collapses to one account.

## Instance: Claude Code oauthAccount

`~/.claude.json` → `oauthAccount` (written by `/login`) overrides `CLAUDE_CODE_OAUTH_TOKEN` env var.
Five sessions showed identical rate-limit usage (14/33) while each had a different token in its env.

## Detection

Identical metrics across sources that should be independent = auth bug, not metrics bug.
Compare against source-of-truth dashboards (claude.ai usage page) — don't trust the toolchain's
own reporting when the toolchain is what you're debugging.

## Prevention

1. After setting up multi-credential: verify by comparing runtime metrics against independent dashboard
2. When a skill/doc answers an auth question: check if it covers the exact product (SDK ≠ CLI)
3. Read own memory before external research — past sessions often have the answer
4. Inspect the config file FIRST, research env var names SECOND

## Connection to past learnings

- 2026-06-08: chain model (pass→.envrc→direnv→claude) finds broken links but not silent overrides
- 2026-06-08: source-code-vs-runtime — reading docs ≠ what actually happens
- 2026-05-08: "`.claude/` is machine-scoped" predicted the collapse to one account
