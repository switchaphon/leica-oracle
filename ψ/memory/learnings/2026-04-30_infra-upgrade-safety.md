---
pattern: Never upgrade shared infrastructure without verifying the dependency chain
date: 2026-04-30
source: "rrr: leica-oracle"
---

# Infrastructure Upgrade Safety

maw v26.4.53 moved 62 plugins to an online registry (`maw.soulbrews.studio/registry.json`) that was unreachable. Result: lost `bud`, `wake`, `ls`, `capture`, `done`, `view` — all critical commands.

## Rule

Before upgrading maw (or any tool the whole team depends on):
1. Read the changelog / release notes
2. `--dry-run` or install in isolation first
3. Verify the 5 most-used commands still work
4. Only then commit to the upgrade
5. Know the rollback command before you start

## Rollback recipe

```bash
bun remove -g maw-js && bun add -g maw-js@github:Soul-Brews-Studio/maw-js#edcf2d5
```

Pinned safe version: `v26.4.31` (commit `edcf2d5` or later pre-registry commits).
