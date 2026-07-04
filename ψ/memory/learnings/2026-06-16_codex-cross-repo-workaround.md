---
name: codex-cross-repo-workaround
description: "When codex team needs to work outside the vet app repo, copy BRIEF to worktrees and use danger-full-access"
metadata:
  type: feedback
---

Codex team charter lives in vet app (`ψ/teams/pops-vet-team.yaml`), but work may target a different directory (e.g. `pops/ai/extract-lab-report/`). The branch isolation model doesn't fit cross-repo work.

**Why:** Codex members spawn in vet app worktrees. `workspace-write` sandbox blocks reading/writing outside the worktree. BRIEF files and output paths outside the repo are invisible.

**How to apply:**
1. Copy BRIEF.md into each worktree before dispatching
2. Use `danger-full-access` sandbox (not `workspace-write`) when output paths are outside the worktree
3. Or create a repo-specific team charter when the work is substantial enough
4. Consider: for pure research (no code changes to vet app), `codex exec` fire-and-forget from the target directory may be simpler than team spawn
