---
source: "rrr: leica-oracle"
date: 2026-05-05
tags: [oracle, mentorship, birth-ritual, permissions, family]
---

# Oracle Mentorship + Birth Ritual Improvements

## Pattern: Oracle-to-Oracle Mentorship

When a new oracle needs to replicate an existing oracle's pattern (e.g. rpro-ent-atlas learning Atlas from pops-atlas):

1. Send mentor a "teach" directive via inbox — explain what student needs to learn
2. Send student a "learn from" mission via inbox — explain who to study and what to ask
3. Student runs `/learn` on mentor's project codebase
4. Student opens `/talk-to mentor` thread with specific questions
5. Mentor responds from knowledge base
6. Leica monitors via `/loop` + `maw peek`

Validated: rpro-ent-atlas asked 6 scaling questions to pops-atlas autonomously after learning.

## Birth Ritual Addition: Pre-approve MCP Permissions

Add to `<oracle>/.claude/settings.local.json` at birth:
```json
{
  "permissions": {
    "allow": [
      "mcp__arra-oracle-v3__arra_threads",
      "mcp__arra-oracle-v3__arra_thread",
      "mcp__arra-oracle-v3__arra_thread_read",
      "mcp__arra-oracle-v3__arra_learn"
    ]
  }
}
```

Without this, every new oracle gets stuck on permission prompts during /talk-to.

## Birth Ritual Addition: Confirm Name First

Always confirm oracle name before writing files. Signal: if user mentions "เดี๋ยวจะมี X อีกตัว" (there will be another X), the naming convention matters — ask first.
