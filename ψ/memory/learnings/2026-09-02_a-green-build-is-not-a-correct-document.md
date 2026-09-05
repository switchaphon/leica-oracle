# A green build is not a correct document

**Date**: 2026-09-02
**Context**: deep-learning the three oracle book skills, and checking them against the
one book this repo has actually published

Asked to learn `/oracle-write-complete-book`, `/oracle-cheatsheet` and
`/oracle-book-cover`, I could have read the three files and written them up. Instead I
ran the pipeline's assumptions against the machine and against the book it already
produced here, `2026-06-17_one-seed-whole-forest`.

Two defects, both in the shipped 58-page PDF, both behind `typst compile` exit code 0:

- The step-5 concat loop emits no separator between chapter files, and no chapter file
  ends with a blank line. Pandoc escapes the leading `#` into the previous paragraph.
  **Ten of eleven chapter headings were destroyed.** The table of contents in the
  published book has one entry, and ten chapters have no page break.
- `Fira Code` is not installed here, so every code block is set in a proportional serif
  and the ASCII trees do not align. Typst warns and exits 0.

The pipeline's only correctness gate is step 9, "read the real PDF with your eyes". It
is manual, it is last, and both defects walked straight through it - because a reader
skimming Thai prose does not count TOC entries or identify a typeface.

**The exit code answered "did the renderer crash", and I had been treating it as an
answer to "is the document right". Those are different questions, and only the first
one is automated.**

The skill also misdiagnoses its own symptom: its fix table blames width for misaligned
ASCII diagrams, when the cause here is a proportional fallback font. A remedy that
points at the wrong dial costs more than no remedy, because it gets followed.

**How to apply:** for any document pipeline, write the assertions that can actually
fail, and put them on the deterministic steps where they are cheap. For this one, five
greps would have caught everything: heading count in the concatenated stream equals the
chapter file count; the same count survives pandoc; no `unknown font` in typst stderr;
`pdffonts` shows a monospace family; page count is what you expected. Verify the
artifact's structure, not the tool's return value.

More generally: when a skill hands me a pipeline, the deep way to learn it is to run its
claims against the machine and against its own past output. Reading it only teaches me
what it intended.

Related: [[api_roundtrip_proves_storage_not_rendering]] - a byte-identical read-back
proves storage, not rendering. Same shape, larger blast radius: here the thing that
"succeeded" was a whole published book.
Related: [[negative-result-needs-positive-control]] - before believing Fira Code was
absent I confirmed the warning fires, that `pdffonts` can see fonts at all, and that the
replacement embeds cleanly.
