# Lesson: Act First, Investigate Second on Visual Regressions

**Date**: 2026-06-11
**Source**: rrr: pops-vet
**Context**: Spent 10 min reading 2,000 lines of code before making a 1-line fix the user had already diagnosed

## Pattern

When a user says "this page should look like that page" and provides both URLs, the fastest correct path is: make the simplest convergence change → verify in browser → then investigate history only if needed. Reading diverged codepaths before acting is wasted time when the fix is "use the correct component."

## Anti-Pattern

Reading hundreds of lines of the broken component to understand what changed, when the user already told you the answer and the fix is a single import swap.

## Rule

1. Trust the user's visual diagnosis
2. Make the smallest change to converge
3. Browser-verify immediately
4. Investigate git history only if the fix didn't work or user wants to know

## Tags

`efficiency`, `visual-regression`, `trust-user`, `browser-first`
