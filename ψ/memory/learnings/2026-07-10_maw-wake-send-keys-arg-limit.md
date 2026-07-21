---
from: leica
timestamp: 2026-07-10T15:02:00+07:00
type: learning
tags: [maw, tmux, debugging, transport]
---

# tmux send-keys has a practical argument length limit

## Pattern

When `maw wake` drains a large inbox (11 messages, 16KB) into the wake prompt, the `sendPromptViaTmux` function passes the entire prompt as a single argument to `tmux send-keys`. This fails with "command too long" because the shell argument (after quoting/escaping) exceeds what the tmux command can handle.

## Root cause chain

1. `isClaudeLikeEngine(undefined)` returns `false` (line 31: `if (!name) return false`)
2. Default wakes (no `--engine` flag) route through the non-Claude path
3. Non-Claude path uses `sendPromptViaTmux` → `tmux.run("send-keys", "-t", target, prompt, "Enter")`
4. `tmux.run()` builds: `tmux send-keys -t <target> <q(prompt)> Enter` and passes to `hostExec("bash -c ...")`
5. With 16KB+ prompt after shell quoting, this exceeds the practical limit

## Fix

`sendPromptViaTmux` now checks prompt length and uses `sendText` (which routes through `tmux load-buffer` via stdin — no size limit) for prompts >4KB.

## Location

Patched locally: `~/.bun/install/global/node_modules/maw-js/src/commands/shared/wake-cmd.ts`
Will be overwritten by npm update — needs upstream PR.

## Lesson

When debugging "too long" errors, don't assume it's ARG_MAX. Trace the full command chain to find which specific tool in the pipeline has the lowest limit. In this case: `tmux send-keys` < `bash -c` < kernel ARG_MAX.
