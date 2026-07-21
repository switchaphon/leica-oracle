---
title: Git is not production for Node-RED projects. `npm run sync` only syncs function 
tags: [nodered, git, drift, flows.json, sync, production]
created: 2026-05-25
source: rrr: nodered-simulator-oracle
project: github.com/switchaphon/nodered-simulator-oracle
---

# Git is not production for Node-RED projects. `npm run sync` only syncs function 

Git is not production for Node-RED projects. `npm run sync` only syncs function code (the `func` field) — it does NOT sync outputs count, wires, new nodes, or node metadata. Before claiming "X doesn't exist in production," export the live flow or ask the user. Stale flows.json in git is not evidence of what's running.

---
*Added via Oracle Learn*
