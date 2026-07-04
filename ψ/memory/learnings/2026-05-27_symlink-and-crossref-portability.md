# Symlinks in public/ must be relative + link targets must be in git

**Date**: 2026-05-27
**Context**: Number format standards docs in pops/vet prototype
**Confidence**: High (verified by reproducing the failure)

## Pattern

When static HTML docs are served by Next.js via a symlink in `public/`:

1. **Symlink must use relative path** — `../../src/app/prototype/docs` not `/Users/switchaphon/.../docs`
   - Absolute paths work on the author's machine only
   - Git stores symlink targets as-is — absolute paths commit the author's home directory

2. **Cross-reference link targets must exist in `public/` (or be served)** — if a doc links to `../../../../../docs/foo.html` and `docs/` is gitignored, the link 404s for everyone else
   - Fix: convert dead links to `<code>` references with "open from repo root" note
   - Or: un-gitignore the target, or move it into the served directory

3. **Verification checklist for doc portability**:
   - No `file://` paths
   - No `/Users/` absolute paths
   - All `href` targets resolve to files tracked in git
   - All `href` targets are inside `public/` (for Next.js serving)
   - Symlinks in git use relative paths

## How it was caught

User said "เปิดลิงค์แล้วมันขึ้น 404" (links show 404 for other developers). `git diff` revealed the symlink stored an absolute path. The gitignored `docs/` cross-references were found by grepping for `hn-vetcode-design` in the HTML files.

## Applies to

Any Next.js project serving static HTML from `public/` via symlinks. Also applies to any git repo with symlinks meant to be portable.
