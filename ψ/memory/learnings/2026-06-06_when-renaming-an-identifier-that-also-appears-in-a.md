---
title: When renaming an identifier that also appears in an import statement, never use 
tags: [tooling, edit-tool, replace-all, import-rename, debugging]
created: 2026-06-06
source: rrr: pops/vet-billing-flow
project: github.com/pops/vet-billing-flow
---

# When renaming an identifier that also appears in an import statement, never use 

When renaming an identifier that also appears in an import statement, never use replace_all — it will catch the import name too and break the module resolution. Use targeted edits: one for the import line, one for body references. Only use replace_all when the string is semantically uniform everywhere (CSS class, string literal).

---
*Added via Oracle Learn*
