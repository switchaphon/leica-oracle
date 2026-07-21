---
title: GitHub Actions CI retrigger: empty commits and close/reopen don't create new che
tags: [github-actions, ci, retrigger, git, devops]
created: 2026-06-05
source: rrr --deep: pawrent-oracle (2026-06-05)
project: github.com/switchaphon/pawrent-oracle
---

# GitHub Actions CI retrigger: empty commits and close/reopen don't create new che

GitHub Actions CI retrigger: empty commits and close/reopen don't create new check suites. GitHub requires a genuinely new commit SHA. The only reliable method: create fresh branch + merge main (git checkout -b new-branch && git merge origin/main). The merge commit produces a new SHA that triggers the pull_request synchronize event. Don't waste time on retrigger tricks.

---
*Added via Oracle Learn*
