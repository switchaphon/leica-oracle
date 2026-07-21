# Learning: Inbox Archive Convention + Fleet-Wide Rename Sweep

**Date**: 2026-07-06
**Context**: Three oracles (pops-vet, rpro-ent, pawrent) all failed `maw wake` with "command too long" due to accumulated inbox messages. Also discovered stale rename refs from Jul 4 rename that were missed.

## Inbox Accumulation

**Problem**: maw drains ALL unread `ψ/inbox/*.md` into the wake prompt. Files are never archived after processing, so they accumulate across sessions until combined content exceeds the shell argument buffer (~128KB on macOS).

**Symptoms**: `HostExecError: [local:local] command too long` on `maw wake`.

**Fix (manual)**: `mkdir -p ψ/inbox/archive && mv ψ/inbox/2026-0[1-6]*.md ψ/inbox/archive/`

**Proper fix (proposed)**: Oracle sessions should archive inbox messages after reading. Convention: on wake, after processing inbox, move processed files to `ψ/inbox/archive/`. Or: maw marks messages as read after drain.

## Rename Sweep Gap

**Problem**: The 9-surface pattern (from [[2026-07-04_oracle-rename-migration]]) doesn't explicitly require a fleet-wide grep across ALL sibling CLAUDE.md files. The Jul 4 rename missed relay-oracle and rpro-saas-oracle.

**Fix**: Add step 7.5 to the pattern:

```bash
grep -rl "old-name" ~/ghq/github.com/switchaphon/*/CLAUDE.md
```

This catches references in oracles you don't remember having cross-references. Do this BEFORE declaring the rename complete.

See [[2026-07-04_oracle-rename-migration]].
