# thClaws Oracle Book Backlog Convergence

## Summary

This issue documents how three AI engines converged on one shared book backlog for the thClaws evolution / thclaws-oracle timeline work.

The engines were:
- **OMX Codex**
- **Claude Code**
- **thClaws Codex** as mediator via `maw hey` and `maw peek`

The important result is that we now have **one canonical backlog**, not multiple competing plans.

---

## Final canonical state

### Canonical GitHub issue set
- **Issues #2–19** on `Soul-Brews-Studio/thclaws-oracle`

### Canonical planning file
- `ψ/writing/thclaws-evolution-book-issues.md`

### Supporting note
- `ψ/writing/book-subtitle-mining.md`

### Superseded plan
- `ψ/writing/thclaws-book-plan.md`

---

## What OMX Codex contributed

OMX produced the stronger long-term structure.

It created:
- the main issue-plan document: `ψ/writing/thclaws-evolution-book-issues.md`
- the canonical issue batch: **#2–19**
- milestone structure
- labels
- chapter issues
- editorial / design / publish meta-issues

It also covered important areas that the alternate Claude batch missed, including:
- **EPIC spine**
- **master timeline appendix**
- **KMS / Research / Memory**
- **The Oracle Mirror**

---

## What Claude Code contributed

Claude initially created a parallel 13-chapter batch:
- **#20–32**

After comparing with OMX's work through `gh`, Claude concluded OMX's backlog was more complete.

Claude then:
- verified issue state with GitHub CLI
- closed duplicate issues **#20–32**
- marked `ψ/writing/thclaws-book-plan.md` as **superseded**
- created `ψ/writing/book-subtitle-mining.md`

That last note is valuable because it preserves the stronger chapter subtitles and phrasing from the duplicate batch instead of losing them.

---

## What thClaws Codex contributed

thClaws Codex acted as the mediator between panes.

It used:
- `maw peek` to inspect real live pane state
- `maw hey` to relay updates between engines

This was what allowed the session to move from confusion to verified convergence.

---

## Why this matters

This session proved that parallel AI planning can converge into a better shared editorial system when:
- one engine builds the stronger canonical structure
- another engine reconciles and preserves useful differences
- a mediator keeps the conversation synchronized with live evidence

The result is better than any one engine's plan alone.

---

## Ready state

The planning phase is now converged enough to begin drafting.

### Current ready state
- one canonical backlog: **#2–19**
- one canonical planning doc: `ψ/writing/thclaws-evolution-book-issues.md`
- one preserved nuance note: `ψ/writing/book-subtitle-mining.md`

### Next action
- begin **Chapter 1** when Nat gives the go-ahead

---

## Suggested follow-up

When writing starts, treat this as the workflow:
1. draft from canonical issues `#2–19`
2. use `book-subtitle-mining.md` for phrasing upgrades
3. keep `thclaws-book-plan.md` as historical context only
