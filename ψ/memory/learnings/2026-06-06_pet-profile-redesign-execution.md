# Lesson: Pet Profile Redesign Execution Patterns

**Date**: 2026-06-06
**Source**: rrr --deep: pops/vet
**Confidence**: High (all patterns observed directly)

## Pattern 1: Grill-First Enables Speed

12 locked decisions (D1-D12) before a single line of code → 6 feature commits in 12 minutes. Zero mid-build design pauses. The grill session was 2.5 hours; execution was 12 minutes. The ratio is correct — design is the bottleneck, not typing.

**When to apply**: Any feature with >3 UI decisions. If you're debating layout during code, you should have grilled first.

## Pattern 2: Audit Existing Patterns Before Creating New

QuickDrawer already had a VN button (FolderOpen + outline style). Built OnBoardBanner with a different icon (ExternalLink + default button). DS had 2-tone outline badges; built VaccinePanel with solid fill. Both caught by user, not by me.

**Rule**: Before creating any button/badge/link that shows data already displayed elsewhere, `grep` for that data pattern (e.g., "VN", "FolderOpen", "border-amber") to find existing implementations.

## Pattern 3: Think Empty State When Creating Mock Data

Created p4/p5 with `rx: [], labs: []` but didn't check if the UI hid empty sections. It didn't — showed empty headers with no content.

**Rule**: For every array field set to `[]` in mock data, immediately check the component that renders it — does it conditionally hide when empty?

## Pattern 4: Post-Commit Checklist Is Non-Negotiable

Skipped DS changelog update on all 9 feature commits. User had to remind. The rule was already in memory from a previous session.

**Rule**: DS DESIGN.md export + CHANGELOG update happens immediately after `git commit`, not "later" or "at the end". No batching. No exceptions. If rushing, that's exactly when you need the checklist most.
