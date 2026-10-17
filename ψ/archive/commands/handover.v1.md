---
description: Write a rich handover doc + emit a thin paste prompt before /clear or /compact
argument-hint: [optional focus hint, e.g. "PRP-16" or "testing-only"]
---

# /handover — Session Handover Generator (doc-first)

**Architecture:** write a rich `.md` handover doc to the current project, then emit a short paste prompt that just points to it.

**Core principle:** *pointer > payload*. The next session has filesystem access — the handover lives on disk as the source of truth; the paste prompt is just a trigger.

**Storage model:**
- This command lives globally (`~/.claude/commands/handover.md`).
- Handover docs are written **per-project** under `<project-root>/.claude/handovers/`.
- Project root = git repo root if in a git repo, else current working directory.

## Optional focus hint from user
$ARGUMENTS

---

## Phase 1 — Resolve project root & prepare storage

```bash
# Git root if available, else cwd
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HANDOVER_DIR="$PROJECT_ROOT/.claude/handovers"
mkdir -p "$HANDOVER_DIR"

# Timestamp for filename + doc metadata
TIMESTAMP="$(date +"%Y-%m-%d-%H%M")"
```

Hold `$PROJECT_ROOT`, `$HANDOVER_DIR`, `$TIMESTAMP` for Phase 4.

The slug (kebab-case, 2-4 words) is synthesized from the session's objective after Phase 2 gathering. Examples: `prp-16-cleanup`, `pawrent-auth-refactor`, `k8s-cert-renewal`.

Final filename: `$HANDOVER_DIR/$TIMESTAMP-$SLUG.md`

---

## Phase 2 — Gather context

Run each step; on failure (not a git repo, file missing, glob empty), skip and continue. **Never abort** the whole command.

### 2.1 Git state

```bash
git branch --show-current 2>/dev/null
git log --oneline -20 2>/dev/null
git status --short 2>/dev/null
git diff --stat 2>/dev/null
```

If working tree is dirty, also run `git diff 2>/dev/null` to understand WIP. Unlike v1 (where prompt size was the bottleneck), there is **no size cap** here — the diff goes into the doc, not the paste prompt, so bloat doesn't hurt the next session's context budget.

### 2.2 PRP / spec files

Globs: `PRPs/**/*.md`, `docs/prps/**/*.md`, `specs/**/*.md`
From this session's conversation, pick the ones **actively referenced**. Record paths only — don't inline content.

### 2.3 Conductor / state files (optional)

Globs: `conductor/**/*.md`, `.conductor/**/*.md`, `docs/state/**/*.md`
If any match AND were discussed this session, note paths only.

### 2.4 TodoWrite snapshot

Review the current TodoWrite list. Map items → `completed` / `in_progress` / `pending`.

### 2.5 Conversation synthesis

Extract from this session's chat:
- **Objective** — what the user ultimately wants accomplished (one line + one paragraph)
- **Decisions locked in** — architectural/design choices this session made that next session must honor
- **Deferred items** — anything explicitly postponed, with reason
- **Blockers / open questions** — stuck points or items awaiting user input
- **Focus narrowing** — if `$ARGUMENTS` is present, use it to narrow which tasks are included

---

## Phase 3 — Synthesize the handover document

Write to `$HANDOVER_DIR/$TIMESTAMP-$SLUG.md`. Use this schema. **Omit empty sections** — never pad with "N/A" placeholders.

```markdown
# Handover: <objective one-liner>

## Meta
- **Timestamp:** <YYYY-MM-DD HH:mm local>
- **Project root:** <$PROJECT_ROOT>
- **Branch:** <git branch or "no git repo">
- **Working tree:** <clean | dirty: N files>
- **Primary reference:** <main PRP/spec path or "none">
- **Focus hint:** <$ARGUMENTS or "none">

## Objective
<one paragraph — what this work stream is ultimately trying to accomplish,
including the "why". Not just the task list. Next session reads this first.>

## Completed this session
<commits made this session (short SHA + subject)
and TodoWrite items marked done. Brief — commits speak for themselves.>

## Remaining tasks
<numbered list, in execution order. Each task:

1. <task id or short descriptor> — <one-line summary>
   **Files:** <paths touched / to touch>
   **Approach:** <2-4 lines of what to do and why>
   **Watch for:** <gotchas, anti-patterns to avoid, specific commands>

2. ...
>

## Uncommitted work in progress        [OMIT if clean]
<file list + git diff --stat output.
If WIP is substantive, include relevant diff hunks inline.
End with: "Decide before continuing: commit, stash, or discard.">

## Constraints
<non-negotiable rules for next session:
- branch rules (e.g. "stay on feature/X, do NOT cut a new branch")
- quality gates (e.g. "run: npm run test && type-check && lint && format:check before each commit")
- anti-patterns (e.g. "do NOT restructure passing pages")
- scope limits (e.g. "task X.Y.Z is deferred — do NOT create it")>

## Deferred / parked                   [OMIT if none]
<items explicitly not being tackled, with reason.
Each: "- <item>: <reason>">

## Key decisions locked in this session   [OMIT if none]
<architectural/design decisions next session must honor.
These are tacit knowledge otherwise lost across /clear.
Each: "- <decision> — <rationale>">

## Open questions / blockers           [OMIT if none]
<stuck points or items awaiting user input.
Each: "- <question>: <context, who/what it depends on>">

## Definition of done
<what "complete" looks like + what to report back to the user
when tasks land. One paragraph.>
```

### Writing rules

- **Exact IDs and paths** — never paraphrase task numbers or file names.
- **Short commit SHAs** (7 chars).
- **Surgical task detail** — enough to execute without re-reading the full PRP; not a PRP copy.
- **Never fabricate** — if uncertain about a path, task ID, or SHA, omit it and note the uncertainty in "Open questions".
- **Respect `$ARGUMENTS`** — if a focus hint was given, narrow "Remaining tasks" to match; move non-matching tasks to "Deferred / parked" with reason "parked per focus hint: `$ARGUMENTS`".

---

## Phase 4 — Emit the paste prompt

After the doc is written, present to chat in this exact shape:

> **Handover saved → `.claude/handovers/<TIMESTAMP>-<SLUG>.md`**
>
> Paste this into the next session (after `/clear` or `/compact`):
>
> ````
> Continue: <objective one-liner> (<N> tasks remaining, branch: <branch>).
> Full handover: .claude/handovers/<TIMESTAMP>-<SLUG>.md
>
> Read the full file first, then proceed with "Remaining tasks" in order.
> Honor all constraints. Report back per "Definition of done".
> ````
>
> <one-line status: e.g. "5 tasks remaining · working tree clean · ready to compact"
> or "3 tasks remaining · ⚠️ WIP in 2 files · review before compacting">

### Paste prompt rules

- **Path is relative to project root** (`.claude/handovers/...`) — clean, portable.
- **One-line teaser** uses the objective one-liner — so if you paste one of several old prompts, you know which is which at a glance without opening the file.
- **"Read the full file first"** is explicit — prevents next session from acting on the teaser alone.
- **Status line** surfaces any blocker that needs attention before `/clear` (WIP, open questions, uncertainty).

---

## Guardrails

- **Never fabricate** task IDs, paths, or commit SHAs. If uncertain → omit + flag in "Open questions".
- **Never inline** full file contents in either the doc or the paste prompt. Paths only (except WIP diffs, which go in the doc).
- **Clean tree** → omit the ⚠️ section entirely. No empty placeholder.
- **No clear objective** (exploratory session) → say so explicitly in the Objective section. Don't invent a goal.
- **Focus hint narrows, never expands** — `$ARGUMENTS` can exclude tasks from the primary list, never add assumptions not present in the session.
- **Self-contained doc** — the written `.md` must stand alone. Next session gets nothing except that file path + filesystem access.
- **No `.gitignore` modification** — solo-dev single-machine workflow; don't touch project `.gitignore`. User can add an entry themselves if ever needed.
