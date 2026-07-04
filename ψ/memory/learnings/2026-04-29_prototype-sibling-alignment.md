# Lesson Learned — Prototype Sibling Alignment via tmux

**Date:** 2026-04-29
**Session:** diagnostic-request-list ↔ pickup-queue-to-opd (parallel Claude panes)
**Repo:** POPs-Vet (`prototype` branch)

## Pattern: Cross-Session Coordination via tmux send-keys

**Confidence: high** (validated by both sessions converging without human relay)

Two parallel Claude sessions in different tmux panes can negotiate shared design tokens, API signatures, and naming conventions by `tmux send-keys` to each other's input boxes. Required incantation:

```bash
tmux send-keys -t '<session>:<window>.<pane>' Escape
sleep 0.2
tmux send-keys -t '<session>:<window>.<pane>' -l "<message text>"
sleep 0.2
tmux send-keys -t '<session>:<window>.<pane>' Enter
```

The `Escape` clears any prior mode; `-l` (literal) prevents shell expansion of special chars; final `Enter` submits.

Verify by `tmux capture-pane -t <target> -p | tail -N` after a poll loop:
```bash
until tmux capture-pane -t '<target>' -p | tail -3 | grep -qE "(Baked|Cooked|Brewed|Sautéed) for [0-9]+s"; do sleep 4; done
```

## Pattern: Mirror-Shape APIs Before Extracting

**Confidence: high**

When two siblings will eventually share a component, both should independently shape it with **identical prop signatures** *before* extraction. Then the extract is a 5-minute lift, not a refactor. Verified today with `FilterDropdown` (`Set<string>` + `onSelectionChange` + `searchable`) and the chip taxonomy (`HnBadge`, `CategoryPill`, `Tag`, `StatusBadge`).

## Pattern: Color Tokens in Consumer, Shape in Shared

**Confidence: high**

Shared chip primitives accept `className` for color tokens (`bg-red-50 text-red-700 border-red-200`); the shared file owns shape + spacing only. Each consumer maintains its domain config map (status → tone, type → tone) locally. Keeps the shared module domain-agnostic and future-proof.

## Pattern: All-Selected = No-Filter

**Confidence: high**

For multi-select filter Sets, treat `selected.size === options.length` as "no filter applied" — short-circuit the `.filter()` call entirely. Gives empty Set unambiguous meaning ("show nothing") and lets indeterminate Minus icon mean "some excluded". Avoids the dead-state where empty and full both pass everything.

## Mistake: Parallel Panes Without File Ownership

**Confidence: high (validated by failure)**

Two Claude agents writing the same file silently overwrite each other. A third anonymous OPD pane today reverted my sibling's chip styles 20 minutes after we agreed on them. The user caught it ("เหมือนยังไม่มีอะไรเปลี่ยน"). 

**Fix going forward:** before spawning parallel panes, declare file ownership — either via a header comment (`// OWNED-BY: <pane-id>`) or a small `OWNERSHIP.md` registry. Two-writer-one-file is the failure mode, not two-writer-nearby-files.

## Mistake: Outer vs Inner Spacing Confusion

**Confidence: high (corrected by user)**

When user mentioned "spacing feels tight", I changed *row vertical padding* (`py-3 → py-5`) when they meant *intra-cell margin* (`mt-1 → mt-2`). 

**Fix going forward:** vertical rhythm has multiple axes. Before adjusting, identify which one:
- Between rows → cell padding (`py-*`)
- Between cells horizontally → cell padding (`px-*`)
- Within a cell, between stacked lines → margin on subsequent line (`mt-*`)
- Within a cell, between flex items → flex `gap-*`

## Mistake: Declared Completion Without Verification

**Confidence: high**

Said "✅ both sessions aligned" before checking the sibling's actually-saved state. The 3rd-pane overwrite went undetected for ~20 minutes. 

**Fix going forward:** when work crosses session/file boundaries, end every "done" claim with a `grep` or `cat` of the actual files. Tool result strings describe intent, not state.

## Reusable Convention: Same Data → Same Header

**Confidence: high**

Shared concepts in sibling tables get the same Thai column header. Established today:
- Pet → `สัตว์เลี้ยง`
- Veterinarian → `สัตวแพทย์`

Distinct events keep distinct names (`วัน/เวลาที่ขอ` vs `เวลานัด/มาถึง`). New shared concepts should be appended to `feedback_column_naming.md`.

## Reusable Convention: Sub-Line Gap = mt-2 (8px)

**Confidence: high (calibrated by user 4→12→10→8)**

Within a table cell that stacks primary + secondary text, use `mt-2` on the secondary div. Calibration trail: too tight at 4px, too loose at 12px, 10px close, 8px picked.

## Connections to Past Learnings

- `read-sibling-prototypes-first.md` (earlier today) → today's session validates this in the **lexical** dimension; sibling pages must converge on words, not just structure
- `reuse-over-rebuild.md` → today's spacing calibration is the spacing-equivalent: don't keep guessing, converge and document
- `commit-early-short-sessions.md` → all of today's work sits uncommitted; flagged as a risk

## Tags

`cross-session-coordination`, `tmux`, `parallel-agents`, `file-ownership`, `chip-extraction`, `prototype-design-system`, `column-naming`, `tailwind-spacing`, `verify-dont-declare`
