---
name: handover
description: 'Use when context is nearly full or work should continue in a fresh session - the user says "handover", "handoff and forward", "handoff here then forward to continue in next session", "pause somewhere safe and hand off", or asks for a handover prompt to paste after /clear.'
argument-hint: "[optional focus, e.g. RPRO-16099]"
---

# /handover

Pause, write the handoff with /forward, commit and push it, then give a short paste prompt. It replaces /handoff's temp file, so /handoff is not called. Context is nearly full when this runs: one document, no full diffs, no re-reading files.

Focus hint (narrows the document, never adds to it): $ARGUMENTS

## 1. Pause at a safe point

- Start nothing new. Finish a short step already under way, so no file is left half-edited.
- Background shells, agents, teammates, CI: wait if one ends within about a minute; otherwise note its ID and how to check it.
- No safe point (a migration or destructive command half done): tell the user what is in flight and stop. Write nothing.

## 2. Write the document

```bash
rtk proxy bash -c 'R=$(git rev-parse --show-toplevel 2>/dev/null || pwd); echo "root: $R"; echo "branch: $(git -C "$R" branch --show-current)"; if [ -e "$R/ψ" ]; then echo "psi: $(readlink -f "$R/ψ")"; else echo "psi: none"; fi; git -C "$R" status --short | head -30; git -C "$R" log --oneline -8; git -C "$R" diff --stat | tail -1'
```

Take the first case that matches:

- **This session already wrote a handover.** Nothing material changed: go to step 4 with that file. Otherwise update that file with one edit and go to step 3.
- **`psi` is a path.** Invoke the `forward` skill with args `--only`; it writes `<psi>/inbox/handoff/YYYY-MM-DD_HH-MM_<slug>.md`. Take only that file from /forward: steps 3 and 4 replace the rest of its flow (plan mode, issues, outbox, commit, closing line). If the file is not under `<psi>/inbox/handoff/`, stop and tell the user where it went.
- **`psi: none`** (product repo). Write the document yourself to `<root>/.claude/handovers/YYYY-MM-DD_HH-MM_<slug>.md`; /forward would create a stray ψ/ here.

Sections, in this order, empty ones dropped:

```markdown
## What We Did          <- each item with its short SHA
## Pending
## Next Session         <- in order: files, approach, watch-outs
## Key Files
## Still Running or Waiting   <- IDs, how to check
## Uncommitted WIP      <- files, then "decide: commit, stash or discard"
## Decisions Locked
## Open Questions
## Suggested Skills
```

Write from this conversation: paths, not file contents; exact IDs and SHAs, and any you are unsure of go under Open Questions. No secret values.

## 3. Commit and push (only when `psi` is a path)

In the repo that holds the real ψ (`git -C <dirname of psi>`):

1. Stage by explicit path: the handoff file plus ψ files this session wrote and has not committed. Files this session did not write belong to other windows and stay unstaged.
2. Scan the staged files with the Grep tool or `rtk proxy grep` (plain grep through RTK can report a false clean) for `(ghp_|github_pat_|glpat-|sk-ant-|sk-proj-|xox[abp]-)[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY`. On a match: unstage, tell the user, stop.
3. Commit only those paths: subject `handoff: <state in one line>` in the session's language, message ending with the Rule 8 signature. Already committed by /forward: skip to the push.
4. Push. When `git rev-list --count @{u}..HEAD` is more than 1 and origin is a github.com URL, the push would also publish commits this handoff did not make, so first run `gh repo view --json visibility -q .visibility` in that repo:
   - `PRIVATE`: push.
   - `PUBLIC`, or gh gives no answer: list those commits (`git log --oneline @{u}..HEAD~1`) and ask the user with AskUserQuestion whether to push them now. Nothing is pushed until the user says push; step 4 reports `push held` with the count.

   Every other case: push. A rejected push: no force, no rebase; it goes in the prompt's last line.

## 4. Reply

The whole reply is two parts:

1. One status line: file path, commit SHA, and pushed, `push held: <N> other commits` (step 3), or `not committed: product repo` (`psi: none`).
2. The paste prompt in a code block, in the session's language:

```
Continue: <objective> (<N> steps left, branch <branch>).
Read <handoff file path, relative to the repo root> first, then do "Next Session" in order.
<only when needed: uncommitted WIP / waiting on X / push failed or held>
```

A window with its own role (worker or sub window, ticket owner) starts the prompt with one role line, e.g. `You are the ENT worker for RPRO-16099 in tmux 05-rpro-ent:6.`
