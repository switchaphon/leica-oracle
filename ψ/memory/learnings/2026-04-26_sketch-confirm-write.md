# Lesson: Sketch → Confirm → Write

**Date**: 2026-04-26
**Source**: rrr — root-oracle session close
**Tags**: workflow, agents, planning, write-discipline

## Pattern

Opening Write tools before the user has confirmed the full architecture leads to rejections and rework. In this session: 3 write rejections, each requiring a clarification exchange before restarting.

## Fix

Before writing any file that is part of a multi-file system (agent files, config, architecture):
1. Sketch the complete plan in text (table, list, or description)
2. Show it to the user
3. Wait for explicit or implicit confirmation
4. Then write all files at once

## Why it matters

Each rejection cycle costs: the rejected write + the clarification exchange + the rewrite. With 8+ interdependent files, one wrong assumption in the first file propagates. Getting alignment before the first Write is always faster than correcting mid-stream.

## The rule

**Never open Write before the user has seen the full plan.**

---

# Lesson: Make infrastructure persistent before ending the session

**Date**: 2026-04-26
**Source**: rrr — root-oracle session close
**Tags**: maw, infrastructure, pm2, persistence

## Pattern

Starting background services with `&` or `maw serve &` creates processes that die when the terminal closes. Leaving persistence as a "next step" means the next session starts broken.

## Fix

Before ending any session that started a background service:
```bash
pm2 start "maw serve" --name maw
pm2 save
pm2 startup  # if not already configured
```

## Why it matters

The next session opens expecting maw to be running. If it's not, every maw command fails silently until the user notices and restarts. The cost of making it persistent now is 30 seconds. The cost of diagnosing a broken session later is much higher.
