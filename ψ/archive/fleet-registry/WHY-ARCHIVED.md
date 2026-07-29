# Why the fleet registry was archived — 2026-07-27

Snapshot of both maw fleet registries taken before repairing the **ghost-window** problem
(`Soul-Brews-Studio/maw-rs#711`, filed by switchaphon 2026-07-27, closed by Nat within 17 hours).
Written retroactively on 2026-07-29 — the archive had been sitting here with no reason attached,
which defeats the point of keeping it.

## What was wrong

After a codex/agent fan-out, every spawned tmux window got recorded in the fleet registry with
the **same `repo` value as the oracle's own window**. maw derives a window's aliases from that
repo, so all siblings inherited identical aliases and `maw wake <oracle>` hard-errored
`ambiguous registry target` **forever**, with no spelling that worked. The windows outlived the
agents that created them.

## The evidence is visible in the filenames

`dot-maw-fleet/` in this archive:

```
07-vets-hub-oracle.json
11-rpro-saas.json        ← index 11 …
11-vets-hub.json         ← … used twice
13-ratchada.json
14-vets-hub.json
15-vets-hub-oracle.json
```

**`vets-hub` appears four times** (07, 11, 14, 15) and **index 11 is claimed by two different
oracles**. That is the collision, preserved as-is.

| | archived here | live after repair |
|---|---|---|
| `~/.config/maw/fleet` | 10 | 10 |
| `~/.maw/fleet` | 7 | 4 |
| oracles.json | 2 files (`config-maw-oracles.json`, `dot-maw-oracles.json`) | — |

## Why it is kept

1. **Recovery.** `~/.config/maw` and `~/.maw` are not git repos. Without this snapshot the
   pre-repair state is unrecoverable.
2. **It is the primary evidence for #711.** If the upstream fix ever regresses, these files show
   the exact shape of the corruption rather than a description of it.
3. **`maw fleet doctor` and `maw fleet gc` both reported "no findings"** while the fleet was hard
   broken. That is recorded in `maw_ghost_windows_break_wake` — do not trust them as a health
   check. The real sweep is `maw wake <o> --dry-run | grep ambiguous`.

## Status of the underlying bug

Fixed upstream in PRs #713–#717 and #723. **Not actually installed here until 2026-07-29 12:37**,
because the binary is fetched from GitHub releases and our note wrongly said "pull + rebuild" —
`git pull` on the source changed nothing while the source tree read as current. Running
`v26.7.28-alpha.1027` since.

Related: `ψ/memory/learnings/2026-07-29_release-vs-source-staleness-and-direnv-non-inheritance.md`,
memory `maw_ghost_windows_break_wake`, `bud_fleet_registration`.
