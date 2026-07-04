---
pattern: "Use Next.js layouts for shared UI across route prefixes — never inline then extract"
concepts: ["next.js layout", "shared components", "route architecture", "DRY"]
source: "rrr: pops-clinic-oracle"
---

When a UI element (breadcrumb, top bar, sidebar) applies to all pages under a route prefix (e.g., `/opd/*`), place it in a `layout.tsx` from the start. Don't inline it in one page and extract later.

**Evidence**: Built OpdTopBar inline in `opd/page.tsx`, committed, then Un pointed out `opd/order-lab` was missing it. Had to extract to shared component, then move to layout — three commits for what should have been one.

**Check**: Before placing a persistent UI element in a page, run `find` or `ls` to check for sibling/child routes under the same prefix.
