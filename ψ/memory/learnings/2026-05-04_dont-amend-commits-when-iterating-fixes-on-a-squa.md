---
title: Don't amend commits when iterating fixes on a squash-merge workflow. Each amend+
tags: [git, amend, rebase, squash-merge, workflow, gitlab]
created: 2026-05-04
source: rrr --deep: nodered-simulator
---

# Don't amend commits when iterating fixes on a squash-merge workflow. Each amend+

Don't amend commits when iterating fixes on a squash-merge workflow. Each amend+force-push creates rebase conflicts when the previous version was already merged to main. Use new commits instead — squash-merge combines them anyway. Amend only when confident it's the final version. This session had 4 rebase conflicts from 5 amend cycles on the same drawtext line.

---
*Added via Oracle Learn*
