---
title: oauthAccount in ~/.claude.json silently overrides CLAUDE_CODE_OAUTH_TOKEN
date: 2026-07-28
source: "rrr: leica-oracle"
concepts: [claude-code, auth, multi-token, oauthAccount, credential-precedence]
---

`oauthAccount` field in `~/.claude.json` (written by `/login` or `claude auth login`) takes
priority over `CLAUDE_CODE_OAUTH_TOKEN` env var. All multi-token sessions silently fall back
to the same account. Fix: remove the field, never `/login` again. The env var name
`CLAUDE_CODE_OAUTH_TOKEN` IS correct — confirmed by docs and testing.

Actual credential precedence: oauthAccount > CLAUDE_CODE_OAUTH_TOKEN > Keychain.

---

## ⚠️ Correction 2026-07-29 — the diagnosis was right, the fix was incomplete

The precedence above is correct and still stands. **"Fix: remove the field, never `/login` again"
was necessary and NOT sufficient** — it was disproven within 24 hours. The field was back on
07-29 as `4trio@oraclenet.org` with Un confirming he had not run `/login`.

**The actual writer:** 8 of 15 oracle repos (chrome, codec, neon, pixel, pops-atlas, relay,
rpro-ent-atlas, vets-hub) had a one-line `.envrc` exporting only `DISCORD_STATE_DIR`.
**direnv loads only the nearest `.envrc` and does not merge with parents**, so having *any*
`.envrc` fully shadowed `~/.envrc`. Those repos ran with **no credential at all**, fell back to
Keychain, resolved to the shared account, and Claude Code then wrote `oauthAccount` back —
poisoning every session opened afterwards.

There was never a mysterious writer. It was ordinary sessions with no token.

**Also missing from the original:** `claude setup-token` writes `oauthAccount` too, exactly like
`/login`. Order matters — run it **before** removing the field, or it silently undoes the fix.

**Complete fix, verified end-to-end:**
1. Give **every** oracle repo an explicit token line (`maw token use <name>` writes it)
2. Remove `~/.envrc` if it exists — it silently defaults every directory under `$HOME`
3. Guard `claude` in `~/.zshrc` against launching with no token (covers *interactive* zsh only)
4. Then remove `oauthAccount`

Result: five accounts with distinct live usage — `trio 14/41 · un 2/36 · por 1/1 · tul 0/24 ·
kla 1/0`. The macOS Keychain entries were removed afterwards as defense-in-depth; **they were
not the fix** — the fix was observed holding before they were touched.

See `2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md` for the full account.
