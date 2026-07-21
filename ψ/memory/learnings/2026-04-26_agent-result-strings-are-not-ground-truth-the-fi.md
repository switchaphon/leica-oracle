---
title: Agent result strings are not ground truth — the filesystem is. When parallel bac
tags: [agents, parallel-execution, filesystem, debugging, background-agents]
created: 2026-04-26
source: rrr: pawrent
project: github.com/switchaphon/pawrent
---

# Agent result strings are not ground truth — the filesystem is. When parallel bac

Agent result strings are not ground truth — the filesystem is. When parallel background agents report misleading summaries ("Prompt is too long"), they may have already written complete output files. Always verify by checking whether the output file exists and has non-zero size before deciding to re-run. The result string is the agent's last utterance, not a status code.

---
*Added via Oracle Learn*
