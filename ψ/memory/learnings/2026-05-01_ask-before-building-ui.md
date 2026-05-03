# Ask Before Building UI the User Hasn't Requested

**Date**: 2026-05-01
**Source**: rrr: leica-oracle
**Confidence**: High

## Pattern

When I have an idea for a UI enhancement (especially for high-visibility surfaces like the statusline), I should show a text mockup and ask before building. The cost of a 2-second question is zero. The cost of building an unwanted feature is the user's time reviewing, testing, and eventually asking to remove it.

## Evidence

Built a 3-line adaptive statusline with dynamic fleet tracking (60+ min). User tried it, said "too much", and asked to remove the fleet line entirely. The version/arra info they actually wanted was hidden in wide-only mode because I used the space for fleet projects.

## Rule

1. Mockup first → ask → build
2. The user's statusline is their most-seen UI — changes must be user-driven
3. "Technically correct" is not the same as "wanted"
