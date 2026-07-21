# Lesson: Direct binary calls beat wrapper abstractions

**Date**: 2026-06-17
**Source**: Leica correction, pops-clinic confirmation
**Context**: Codex invocation in pops-vet

## Lesson

When a CLI binary works correctly on its own (`codex exec`), adding wrapper layers (`maw team up` with `engine: omx`) introduces failure modes that don't exist in the direct call — stale state, ambiguous dispatch, hidden configuration. The wrapper's convenience is not worth debugging its edge cases.

## Application

- Default to the simplest invocation path for external tools
- If a wrapper fails once, prefer the raw binary permanently rather than patching the wrapper
- For parallelism, use OS-level primitives (tmux panes) rather than tool-level orchestration
- When updating memory about tool invocation, preserve the WHY (save Claude tokens) and update the HOW (codex exec, not omx)
