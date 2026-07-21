---
title: React hooks must ALL be called before any early return in a component. Placing u
tags: [react, hooks, hydration, prototype, debugging]
created: 2026-05-14
source: rrr: pops-clinic-oracle
project: github.com/switchaphon/pops-clinic-oracle
---

# React hooks must ALL be called before any early return in a component. Placing u

React hooks must ALL be called before any early return in a component. Placing useState/useEffect after `if (!mounted) return null` causes "Rendered more hooks than during the previous render" crash. Hook call order must be identical across every render — move all hooks to the top, use their values conditionally in JSX instead.

---
*Added via Oracle Learn*
