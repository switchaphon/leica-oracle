---
title: When renaming a directory in a project: (1) Always `git checkout -b` BEFORE comm
tags: [git, rename, dockerfile, pipeline, conductor, pattern-adoption]
created: 2026-05-04
source: rrr: nodered-simulator
---

# When renaming a directory in a project: (1) Always `git checkout -b` BEFORE comm

When renaming a directory in a project: (1) Always `git checkout -b` BEFORE committing — committing on main then branching creates identical branches and an empty MR. If main is protected, you can't force-push to fix it. (2) Dockerfile COPY paths embed source directory names as strings — grep file contents, not just filenames, when building a rename map. (3) When adopting a pattern from another project, read integration points (how CLAUDE.md references it, styleguides subdirectory) not just the standalone files.

---
*Added via Oracle Learn*
