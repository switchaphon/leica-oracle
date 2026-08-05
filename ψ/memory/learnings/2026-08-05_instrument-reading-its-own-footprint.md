# A capable instrument still lies if it reads its own footprint

**Date**: 2026-08-05
**Confidence**: HIGH — three independent sightings in 90 minutes, all reproduced
**Sharpens**: `2026-08-05_a-test-must-be-able-to-detect-the-thing.md` (same day, earlier session)
**Also sharpens**: `2026-07-30_five-ways-a-secret-scan-lies.md` (Lie 4), `2026-07-31_did-i-break-it-un-make-the-change.md`

---

## The gap this fills

The rule written this morning asks: **can this instrument detect the thing at all?** A route table cannot see a SOCKS tunnel; there is no positive reading to hope for. That rule catches *blind* instruments.

It does not catch the case where the instrument **can** see the thing and still reports the wrong answer — because it read a channel that the checking process itself had just written to, or that carried state from before the check began.

**Second question, now mandatory:**

> What else could produce this exact reading — my own action, inherited/cached state, or a same-shaped-but-wrong object — independent of the real thing?

---

## Three sightings, one session

| # | instrument | shared channel | what got matched instead of the signal |
|---|---|---|---|
| 1 | `wait_for BOTUP` in a tmux pane | the pane's text stream | **my own typed command.** `tmux send-keys` echoes what it types, so the pattern matched the command line before the output existed |
| 2 | `direnv export bash` | the process environment | **state from before the check.** `DIRENV_DIFF` was already set, so direnv correctly printed nothing — read as "direnv is broken" instead of "already applied" |
| 3 | a `ps`-based pre-flight scan | process/window namespace | **a generic proxy** disagreed with the exact first-party query. The proxy said the bot was down; it was running |

Sighting 1 is the sharpest, because it was written **into the script whose purpose was to prevent this class of failure**, in the same session that diagnosed it.

The same shape a second time in sighting 1: waiting for `plugin:discord@claude-plugins-official` — a string sitting inside the launch command just sent. Both the probe and the confirmation read the echo.

---

## Countermeasures (all cheap)

1. **Anchor past your own echo.** `^BOTUP [0-9]` not `BOTUP`. Verify with a **negative control**: feed it the echoed command and confirm it does *not* match.
2. **Match text only the target produces.** `inject directly` (the banner's own words), never the channel name that also appears in your command.
3. **Take a fresh read.** `env -i HOME=… PATH=…` to strip inheritance. A shell that already has the state cannot tell you whether the state loads.
4. **Prefer the first-party registry over a proxy.** `tmux list-windows … grep -qx "$WIN"` beats counting `ps` output whenever the two can disagree.
5. **Ask what the far end saw.** `exit 0` is the actor's own testimony. So is a channel banner: it proves the token *loaded*, never that the issuer *accepted* it.

---

## Two facts worth their own line

**`set -a; source file` is a clobber, not a fallback.** It assigns unconditionally and overrides an already-exported value. This is how twelve launchers resurrected rotated Discord tokens. The correct idiom is the Discord plugin's own (`server.ts:48`):

```js
if (m && process.env[m[1]] === undefined) process.env[m[1]] = m[2]   // fill gaps, never overwrite
```

**Non-interactive shells get no `.envrc`.** The direnv hook lives in `~/.zshrc`; `bash script.sh` never fires it. A launcher must run `eval "$(direnv export bash)"` itself, then guard: `: "${VAR:?…}"`.

---

## The meta-failure

`2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md` §5 already recorded that `CLAUDE_CODE_OAUTH_TOKEN` is stripped from subprocess environments — *"never verify an action with the tool that performed it… do not ask them."* I rediscovered it at cost five days later, mid-investigation.

**The memory was right and I measured instead of reading it.** Before spending verification budget on a tool/env interaction, grep `ψ/memory/learnings/` for the tool name first. The cheapest control is the one already written down.
