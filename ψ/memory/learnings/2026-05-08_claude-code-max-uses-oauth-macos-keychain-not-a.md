---
title: Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting
tags: [claude-code, auth, security, multi-account, oauth]
created: 2026-05-08
source: rrr: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting

> ## ⛔ PARTIALLY SUPERSEDED 2026-08-05 — do not run the `claude auth logout` → `login` advice
>
> **"Native `claude auth logout` → `claude auth login` is the safest multi-account approach"
> is the single most damaging instruction in this brain.** That command writes `oauthAccount`
> into `~/.claude.json`, which **outranks `CLAUDE_CODE_OAUTH_TOKEN`** and silently collapses
> every session onto one account. It caused a two-day outage across 15 oracles.
>
> Switch with **`maw token use <name>`** + restart the session. Never `/login`.
>
> **Why this banner is late.** The correction was written on 2026-07-29 onto
> `2026-05-08_claude-code-multi-account.md` — the longer sibling saying the same thing. This
> shorter file was auto-ingested via Oracle Learn and the correction pass never touched it, so
> the bad advice stayed live and greppable for a week. Found 2026-08-05 by an agent sweeping
> memory during `/rrr --deep`.
>
> **The rule that generalises:** a correction must be applied to every file carrying the claim,
> not just the one you were reading. Grep the claim, not the filename.
>
> See `2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md` and the correction
> section of `2026-05-08_claude-code-multi-account.md`.

Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting ANTHROPIC_API_KEY don't work with Max. The .claude/ folder is machine-scoped — settings, skills, memory persist across account switches. ~~Native `claude auth logout` → `claude auth login` is the safest multi-account approach.~~ **← FALSE, see banner.** Third-party token managers store OAuth in plaintext — unnecessary risk for infrequent switching.

---
*Added via Oracle Learn*
