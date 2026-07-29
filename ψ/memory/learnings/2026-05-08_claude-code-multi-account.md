# Claude Code Multi-Account Switching

> ## ⛔ PARTIALLY SUPERSEDED 2026-07-29 — do not run item 4
>
> **Item 4 ("Native switching = `claude auth logout` → `claude auth login` — safest") is now the
> single most damaging instruction in this brain.** That command writes `oauthAccount` into
> `~/.claude.json`, which **outranks `CLAUDE_CODE_OAUTH_TOKEN`** and silently collapses every
> session onto one account. It caused a two-day outage across 15 oracles.
>
> **Item 6 ("No native multi-profile support") is also false** — env-var tokens work fine once
> `oauthAccount` is absent. Verified 2026-07-29: five accounts reporting distinct live usage.
>
> Switch with **`maw token use <name>`** + restart the session. Never `/login`.
> See the correction section at the bottom and
> `2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md`.

**Date**: 2026-05-08
**Source**: Research session — Un has 2 Max accounts
**Tags**: claude-code, auth, security

## Key Facts

1. **Max plan uses OAuth** (macOS Keychain), not API keys — proxy tools expecting `ANTHROPIC_API_KEY` don't work with Max subscriptions
2. **`.claude/` folder is machine-scoped** — settings, skills, memory, CLAUDE.md all persist across account switches. Only the OAuth token changes.
3. **Claude Code proxy projects** (1rgs, fuergaosi233, agentgateway) solve model routing (use Gemini/GPT through Claude Code), NOT account switching
4. **Native switching** = `claude auth logout` → `claude auth login` — safest, no dependencies
5. **Third-party tools** (claude-swap, CCS) exist but store OAuth tokens in plaintext — unnecessary risk for infrequent switching
6. **No native multi-profile support** — feature request open at anthropics/claude-code#44687

## Pattern

When evaluating third-party auth tools: if the native approach takes 10 seconds and the tool saves you 8 of those seconds but requires trusting a stranger with your OAuth tokens — the native approach wins.

---

## Correction — 2026-07-29

**What held up.** Item 2 was the most prescient line here: *"`.claude/` is machine-scoped — only
the OAuth token changes."* That predicted the collapse-to-one-account failure two and a half
months before it happened, and it is still the reason `CLAUDE_CONFIG_DIR` (aliased in
`~/.zshrc:141-142` but never actually created) remains the structural alternative. Item 5's
caution about plaintext token storage also held — that is why tokens live in `pass` and why
removed Keychain values were deliberately not backed up.

**What broke.** Items 4 and 6. The research was done before `oauthAccount` existed as a
consideration, so "logout → login" looked like the clean path. It is the opposite: it is the
*only* thing that reliably re-breaks multi-account setups.

**The correct model, verified end-to-end:**

```
precedence:  oauthAccount (~/.claude.json)  >  CLAUDE_CODE_OAUTH_TOKEN  >  macOS Keychain
switch:      maw token use <name>   then restart the session
never:       /login · claude auth login   (both write oauthAccount)
careful:     claude setup-token also writes it — run it BEFORE removing the field, never after
```

Each oracle repo needs its own token line, because **direnv loads only the nearest `.envrc` and
does not merge with parents** — a one-line `.envrc` for an unrelated variable silently drops the
credential you assumed was inherited. That was the actual root cause of the 07-28/07-29 outage.

**Meta-lesson.** This file sat unchanged for 82 days while its item 4 quietly became a landmine.
Nothing marked it. Research notes need re-validation dates the same way plans do — a correct
answer from May is not a correct answer in July, and the note gives a reader no way to tell.
