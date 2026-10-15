# oracle-book-skills Learning Index

## Source

Three skill files, given as `~/Downloads/oracle-{writecompletebook,cheatsheet,bookcover}.md`.
All three are **byte-identical** to copies already installed at:

- `~/.claude/skills/oracle-write-complete-book/SKILL.md`
- `~/.claude/skills/oracle-cheatsheet/SKILL.md`
- `~/.claude/skills/oracle-book-cover/SKILL.md`

Nothing needed installing. This was comprehension work.

Related prior art in this repo:
- `ψ/writing/books/2026-06-17_one-seed-whole-forest` - the one book built with this pipeline
- `ψ/writing/cheatsheets/2026-06-19_workshop-06-opstack-l2-sepolia.md`

## Explorations

### 2026-09-02 1309 (deep)

- [[2026-09-02/1309_ARCHITECTURE|Architecture]] - the three skills as one pipeline
- [[2026-09-02/1309_CODE-SNIPPETS|Code Snippets]] - runnable parts, corrected
- [[2026-09-02/1309_QUICK-REFERENCE|Quick Reference]] - which skill when
- [[2026-09-02/1309_TOOLCHAIN-REALITY|Toolchain Reality]] - what exists on mba
- [[2026-09-02/1309_TRAPS-AND-GAPS|Traps and Gaps]] - two shipped bugs

Two of the five standard `--deep` lenses were substituted: these skills have no test
suite and no API, so TESTING became TOOLCHAIN-REALITY ("will it run here?") and
API-SURFACE became TRAPS-AND-GAPS ("where does it fail?"). The fan-out was also skipped
- 760 lines of markdown fit in context, so five Haiku agents would have summarised what
I could read directly. Time went into verification instead.

**Key insights**:

1. **The pipeline's success signal is broken.** `typst compile` returns 0 on a missing
   font. Every gate in the pipeline is manual and last. Two defects reached a published
   book behind a green exit code.

2. **The step-5 concat loop destroys chapter headings.** No separator is emitted between
   files, no chapter file ends with a blank line, so pandoc escapes `#` into the previous
   paragraph. The shipped 58-page book has a table of contents with **one entry** and no
   chapter page breaks. Reproduced and fixed.

3. **`Fira Code` is not installed here**, so every code block in the shipped book is set
   in a proportional serif. The skill's own fix table blames width for the misaligned
   ASCII trees, which points away from the real cause. `JetBrains Mono` verified as a
   drop-in.

4. **The skill's `thai-wordbreak.py` is missing its `__main__` block** - copied as
   printed it defines a function and does nothing.

5. **The three skills are not a set.** Write-complete-book and book-cover compose through
   exactly one typst block. Cheatsheet shares nothing with either; it only mines the same
   session JSONL.
