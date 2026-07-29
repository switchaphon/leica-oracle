# Keychain entries removed — 2026-07-29

Removed after multi-token was verified working via `CLAUDE_CODE_OAUTH_TOKEN`.
Values were NOT backed up: writing credentials to disk in cleartext is the exact
problem recorded in `prompt_history_leaks_secrets`. Only metadata is kept here.

| service | acct | created | last modified |
|---|---|---|---|
| `Claude Code-credentials`          | switchaphon | 2026-07-28 09:22 +07 | 2026-07-29 09:30 +07 |
| `Claude Code-credentials-0aaec709` | switchaphon | 2026-05-13 16:57 +07 | 2026-05-13 16:57 +07 |
| `Claude Code-credentials-5389bbb4` | switchaphon | 2026-05-06 15:31 +07 | 2026-05-07 09:19 +07 |
| `Claude Code-credentials-b5ee3da1` | switchaphon | 2026-05-29 15:33 +07 | 2026-05-29 15:33 +07 |

Not removed: the two `Claude Safe Storage` items — those belong to the Claude
desktop app, unrelated to Claude Code CLI auth.

**Why removed.** They were the fallback a credential-less session resolved to, which is
how `oauthAccount` kept getting rewritten as trio. The `~/.zshrc` guard only covers
*interactive* zsh — `.zshrc` is not sourced by scripts, cron, or `zsh -c` — so removing
the reservoir is the only structural close of that path.

**Restoring one costs a `/login`,** which writes `oauthAccount` back and would have to be
cleaned up again. Un's call, made with that tradeoff stated: "ลบทิ้งเลย แตกเดี๋ยวรู้กัน".

**What to watch:** anything launching `claude` outside an oracle repo, or outside an
interactive shell, now has no credentials at all and should fail loudly instead of
silently authenticating as trio. That loud failure is the intended behaviour.
