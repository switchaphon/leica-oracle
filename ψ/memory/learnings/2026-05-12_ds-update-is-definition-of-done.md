---
date: 2026-05-12
session: opd-standalone-layout-ds-changelog
source: user feedback
---

# DS Update Is Definition of Done

When any prototype UI introduces a new layout variant, component pattern, or navigation behavior, the design system page must be updated in the same commit. Don't ask — just do it.

The DS serves two audiences:
1. Humans reviewing the visual reference
2. AI tools consuming the downloadable .md for code generation

Both break if the DS falls behind the prototype code.

**Trigger**: Any change to layout, top bar, component variants, or navigation patterns.
**Action**: Update the relevant DS section + add a changelog entry + update DS_LAST_UPDATED + update DS_MARKDOWN.
