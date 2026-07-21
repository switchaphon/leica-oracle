---
title: Never call a state setter inside another React state updater callback. React str
tags: [react, state-management, anti-pattern, strict-mode, cross-state-coordination]
created: 2026-05-19
source: rrr: pops/vet — X-ray order extremity delete crash 2026-05-19
project: github.com/switchaphon/pops-clinic-oracle
---

# Never call a state setter inside another React state updater callback. React str

Never call a state setter inside another React state updater callback. React strict mode can re-invoke updaters, causing TypeError on already-deleted state. Use a closure variable (e.g. `let willBeEmpty = false`) to communicate intent out of the updater, then call the second setter after the first returns. Always add a guard (`if (!site) return prev`) for re-invocation safety.

---
*Added via Oracle Learn*
