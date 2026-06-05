# maw wake — correct oracle spawn command

**Date**: 2026-06-05
**Source**: rrr: leica-oracle
**Tags**: maw, cli, fleet, orchestration

## Pattern

The correct maw command to start an oracle session is:

```bash
maw wake <oracle-name>    # spawns tmux session, auto-clones if needed
maw hey <oracle-name> "<msg>"  # send message to running oracle
maw peek <oracle-name>    # read oracle's screen
maw a <oracle-name>       # attach to oracle session
```

`maw workon` does NOT exist. Memory cheatsheet was stale.

## Lesson

After multi-week gaps, always `maw --help` before assuming command names from memory. CLIs evolve between sessions — verify before executing.

## Anti-pattern

Reporting "oracle is ready" without peeking first. Always peek after `maw hey` to confirm the oracle actually responded before telling the human it's alive.
