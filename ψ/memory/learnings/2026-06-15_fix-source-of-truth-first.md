# Fix Source of Truth First, Derivatives Second

**Date**: 2026-06-15
**Source**: CLAUDE.md path fix session
**Tags**: documentation, drift, source-of-truth

## Pattern

When a documentation error appears in multiple places, trace it back to the source and fix that first. Fixing derivatives without fixing the source means the next generation of docs re-inherits the same errors.

## Evidence

AGENTS.md + agents/*.md had 8 wrong paths. All came from CLAUDE.md. Fixing only the agent files would have been undone on the next Leica deploy or deep-learn refresh.

## Rule

1. Trace the error to its origin (usually CLAUDE.md for this project)
2. Fix the origin first
3. Then fix or regenerate derivatives
4. If you can only fix derivatives now, leave a TODO at the source — don't pretend the job is done
