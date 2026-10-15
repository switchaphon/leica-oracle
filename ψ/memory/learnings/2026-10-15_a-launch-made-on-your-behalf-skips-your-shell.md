---
name: a-launch-made-on-your-behalf-skips-your-shell
description: "We knew since 2026-08-05 that a tmux pane started with a command runs under `sh -c` with no direnv. It bit again on 2026-10-15 because Claude Code made that launch for us, when it spawned agent-team teammates. The tell was a token that was absent, not empty. Ask whose shell runs a process you did not launch yourself."
metadata:
  type: learning
---

# A launch made on your behalf skips your shell

## What happened

rpro-ent spawned four reviewer teammates in tmux for the RPRO-15992 CI review. All four died at once:

```
Teammate @ci-security-review failed: Not logged in · Please run /login
```

The lead was logged in on `CLAUDE_CODE_OAUTH_TOKEN`, which direnv loads from `.envrc` through `pass`. rpro-ent blamed gpg and unlocked it, but the teammates still died. Then it concluded that the panes took their env from the lead process.

The Claude Code binary (2.1.296, the same in 2.1.300) shows what happens instead:

```
tmux split-window -d -t <lead pane> -h -l 70% -P -F '#{pane_id}' -- cat
tmux respawn-pane -k -t <pane> -- "cd <cwd> && env CLAUDECODE=1 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 <forwarded> <claude> --agent-id ..."
```

tmux runs that string with `/bin/zsh -c`. That shell is non-interactive, so `.zshrc` never runs and neither does the direnv hook. The env comes from the tmux server, which held only PATH and SHELL. `<forwarded>` is a fixed list of Bedrock, Vertex, proxy and CA variables, and the OAuth token is not on it. The teammate inherits from the tmux server, never from the lead.

## Why it happened

**We had already written the rule down.** On 2026-08-05, [[source-clobbers-direnv]] says:

> `tmux new-window -c dir` with **no command** starts an interactive shell and direnv fires.
> Passing the command to `new-window` runs it under `sh -c` — direnv never loads.

That note was written for our own launchers, such as `start.sh` and bot windows. Here the launch lived inside a tool, two layers down. Nobody pictured a `respawn-pane` with a command string, because nobody typed one. **A rule you learned for your own launches does not protect you from launches made on your behalf.** Claude Code, maw, cron, launchd and plugin servers all start processes that never run your `.zshrc`.

## The tell: absent, not empty

rpro-ent's measurement held the answer before anyone read the binary. `ps eww` on a teammate showed **no `CLAUDE_CODE_OAUTH_TOKEN` at all**.

| what the process has | what it means |
|---|---|
| variable present, length 108 | the env loaded |
| variable present, empty | direnv ran and the command inside `.envrc` failed (gpg locked, pinentry timed out) |
| **variable absent** | **no shell that loads `.envrc` ever ran in this process's ancestry** |

An empty value sends you to the credential store. An absent one sends you to the launch path. I almost read past the difference: I took the direnv lines in the scrollback for teammate output, when they were the lead pane's own history.

Length alone cannot answer the next question, which is whether it is the right token. Every token is 108 characters, so compare a sha256 prefix.

## The fix, and the trap inside it

- `CLAUDE_CODE_TEAMMATE_COMMAND` in the settings `env` points at `~/.claude/bin/claude-teammate`. The wrapper runs `eval "$(direnv export zsh)"`, fails loud with no token, and execs claude.
- It is undocumented and absent from the docs. It is present in the binary in 2.1.296 and 2.1.300.
- Settings `env` reaches running sessions. Two sessions started before the edit both used the wrapper.
- **The trap:** I first copied `unset DISCORD_BOT_TOKEN` from rpro-ent's headless launcher, where `--strict-mcp-config` made it harmless. In a teammate, the Discord plugin falls back to `$DISCORD_STATE_DIR/.env` when the token is `undefined`, and the global settings aim that at leica's directory. The precaution could have logged a worker in as the wrong bot. `DISCORD_BOT_TOKEN=""` closes the fallback, because empty is not undefined.

## How to apply

1. For any process you did not launch with your own keystrokes, ask **whose shell ran it**. In tmux, `#{pane_start_command}` answers it: non-empty means `sh -c`, so no `.zshrc` and no direnv.
2. Measure presence separately from length, and length separately from identity: present, length, then hash prefix.
3. Never answer a teammate's "Please run /login". It writes `oauthAccount` and collapses every session onto one account ([[multi-token-fix]]).
4. Before importing a precaution from another launcher, check what the consumer does in the case you are creating. Unset and empty are different cases for most loaders.

Related: [[teammate-tmux-no-token]] (the auto-memory with the full mechanism), [[negative-result-needs-positive-control]]. In this session the positive control caught a harness that had silently lost the output.
