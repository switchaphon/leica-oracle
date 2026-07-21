# Lesson: Survey all branches before building new artifacts

**Date**: 2026-07-03
**Source**: CRM migration session — built Dockerfile + CI + health endpoint on main, then discovered refactor/drizzle-stack branch had superior versions already (50 commits, production-tested)
**Confidence**: High (burned ~1 hour of redundant work)

## Pattern

Before creating any deployment artifact (Dockerfile, CI config, k8s manifest, health endpoint) in an unfamiliar repo:

```bash
git branch -a
git log --all --oneline -30
```

Feature branches may contain weeks of completed work that main doesn't reflect. Prototyping repos (v0-*, my-project) especially — the "real" stack is often on a branch.

## Related patterns

- Ask about the **target architecture**, not just the current code. "We are not using Supabase" invalidated an entire env var design that matched the source code perfectly.
- The `v0` in a repo name is a signal: this was scaffolded, not architected. Expect divergence between main and branches.

## Reusable

Add to any codebase exploration checklist: "What's on other branches?" before "What does the code do?"
