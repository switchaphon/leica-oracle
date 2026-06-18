# [PROJECT NAME] — Codex Agent Context

> [One-line description of what this project is]

## Stack

- [Framework + version]
- [Language + mode]
- [Styling]
- [Data fetching]
- [Auth]
- [Testing]
- [Package manager + Node version]

## Hard Rules

1. **[Rule about file boundaries]** — what Codex can/cannot touch
2. **Never run** `git add`, `git commit`, `git push`. Edit files only. The lead reviews and commits.
3. **Never install packages** without explicit approval.
4. **[Project-specific patterns that must be followed]**
5. **[Code style conventions]** — indent, quotes, etc.

## Architecture Gotchas

### [Gotcha 1 — e.g. Auth Model]
[Explain the non-obvious thing that will trip up any agent]

### [Gotcha 2 — e.g. State Management]
[Explain the pattern that differs from "obvious" approach]

### [Gotcha 3 — e.g. Build Constraints]
[Explain any size/performance/compatibility constraints]

## File Structure

```
src/
├── [describe your layout]
└── [key directories and what they contain]
```

## Role Agents

For role-specific context, see:
- `agents/chrome.md` — frontend patterns
- `agents/flux.md` — backend/API patterns
- `agents/static.md` — testing patterns

## Reporting

When done with a task:
1. Print `DONE:` followed by a per-file summary of changes
2. List any unused imports you removed
3. Flag anything you were unsure about with `QUESTION:`
