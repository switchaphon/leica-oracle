---
type: learning
date: 2026-06-07
source: "rrr: pops-clinic-oracle"
concepts: [css, overflow, tabs, tailwind, pet-profile]
---

# overflow-x-auto kills -mb-px tab gap trick

CSS spec: when `overflow-x` is set to anything other than `visible`, the computed value of `overflow-y` becomes `auto` (not `visible`). This means `-mb-px` on child elements gets clipped vertically, breaking the Chrome-tab "gap in bottom line" effect.

**Fix**: Don't use `overflow-x-auto` when you need `-mb-px` overlap. For prototypes with a known small number of tabs (4-5), just use a normal flex row. Scroll + fade is premature optimization that blocks the design goal.

**Also learned**: For visual polish sessions, parallel agents are good for initial build but sequential inline edits win for iterative refinement. Each tweak needs to see the previous result — tight feedback loops beat parallel agents.
