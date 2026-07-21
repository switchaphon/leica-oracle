---
title: maw hey works — fleet config name must match tmux session names exactly. resolve
tags: [maw-hey, fleet-config, session-naming, routing, debugging]
created: 2026-05-08
source: rrr: leica-oracle 2026-05-08
project: github.com/switchaphon/leica-oracle
---

# maw hey works — fleet config name must match tmux session names exactly. resolve

maw hey works — fleet config name must match tmux session names exactly. resolveFleetSession reads config.name from fleet JSON, matches against tmux sessions. If session has numeric prefix (e.g. "04-neon"), fleet config must say "04-neon" not "neon". Fix: update ~/.config/maw/fleet/*.json name fields. Issue #1141 was already fixed by Nat (PRs #1107, #1136, #997).

---
*Added via Oracle Learn*
