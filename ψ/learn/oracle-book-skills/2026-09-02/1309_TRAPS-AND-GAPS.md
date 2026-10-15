# Traps and gaps - two silent bugs, both shipped

Substituted for the `--deep` API-SURFACE lens. These skills expose no API; what they
expose is a failure surface, and it is bigger than the skills admit.

Both bugs below are **present in the one book already published from this machine**,
`ψ/writing/books/2026-06-17_one-seed-whole-forest` (58 pages, rendered 2026-06-17).
Both produce `typst compile` exit code 0.

---

## Bug 1 - the concat loop destroys chapter headings (severe)

### What the skill says

Step 5, verbatim:

```bash
for f in 00-*.md 01-*.md ... 15-*.md; do
  uvx --from pythainlp python3 thai-wordbreak.py "$f" >> /tmp/book-zwsp.md
done
```

No separator is emitted between files.

### What actually happens

Every chapter file in the shipped book starts with `# ` and **none ends with a blank
line** (checked all 11). So concatenation produces:

```
...Oracle School session 2026-06-15*
# กับดัก ESPHome
```

Pandoc's markdown will not start an ATX heading on a line that continues a paragraph.
It escapes it instead. Reproduced exactly:

```
$ pandoc broken.md -t typst
= Chapter One
<chapter-one>
body text of one \# Chapter Two     <- heading swallowed, escaped to literal '#'

body text of two
```

### The damage in the shipped book

- The table of contents has **one entry** for an eleven-file book. `#outline(depth: 1)`
  had only one level-1 heading to find.
- Ten chapters got **no page break**. `#show heading.where(level: 1)` never fired for
  them, so the `pagebreak(weak: true)` never ran.
- Ten literal `#` characters render mid-sentence. Visible on page 1:
  `Oracle School · The Circuit · 2026 # zip ไฟล์เดียว`, and on page 13:
  `Oracle School session 2026-06-15 # กับดัก ESPHome`.

A 200-page book with no working table of contents and no chapter breaks, built and
published with a green exit code.

### Fix (validated)

```bash
for f in 0*.md 1*.md; do
  uvx --from pythainlp python3 thai-wordbreak.py "$f"
  printf '\n\n'
done > /tmp/book-zwsp.md
```

Note also `>` on the loop rather than `>>` per file - the skill's `>>` appends to
whatever the last run left behind. Re-running it twice doubles the book.

### Guard

```bash
# heading count in the concatenated stream must equal the file count
grep -c '^# ' /tmp/book-zwsp.md
pandoc /tmp/book-zwsp.md -t typst | grep -c '^= '
ls 0*.md 1*.md | wc -l          # all three numbers must match
```

---

## Bug 2 - the code font does not exist here

### What the skill says

`book.typ`, both raw rules: `set text(font: "Fira Code", size: 9pt)`.
The font table lists it as `brew install --cask font-fira-code`.

### What actually happens

`Fira Code` is not installed on mba. Typst prints

```
warning: unknown font family: fira code
```

and **exits 0**. Code falls back to the default proportional serif.

### The damage in the shipped book

`pdffonts book.pdf` on the 58-page PDF lists Sarabun (4 weights), LibertinusSerif,
ArialMT, K2D, SFNS, AppleColorEmoji - and **no monospace font at all**.

Rendered page 13 shows the effect: the directory-tree code block is set in serif, so
the `├──` box-drawing characters do not line up. Inline code such as `CMakeLists.txt`
renders as tiny serif text rather than mono.

### The skill misdiagnoses its own symptom

Its Common Fixes table says:

| ปัญหา | แก้ |
|--------|-----|
| ASCII diagram border ไม่ align | ปรับ width ให้พอดี code block |

Adjusting width can never align an ASCII tree set in a proportional font. The remedy
treats the symptom and points away from the cause. Anyone following the table will
burn iterations on the wrong dial.

### Fix (validated)

Either install the font, or use one that exists:

```typst
set text(font: "JetBrains Mono", size: 9pt)
```

Verified: no warning, exit 0, `JetBrainsMono-Regular` embedded, ASCII tree aligned.

### Guard

```bash
typst compile book-full.typ book.pdf 2>&1 | grep -i "unknown font" && echo "FALLBACK"
pdffonts book.pdf | grep -iE "mono|code|menlo|courier" || echo "NO MONO EMBEDDED"
```

---

## The shared root cause

Both bugs share one property: **the pipeline has no verification step that can fail.**

Step 9 says "ตรวจด้วยตา (อ่าน PDF จริง)" - check with your eyes, read the real PDF.
That is the only gate, it is manual, and it is last. Both defects survived it, because
a Thai reader skimming for prose quality does not count TOC entries or identify a
typeface.

Every deterministic step should assert:

| Step | Assert |
|------|--------|
| 5 concat | heading count in stream == chapter file count |
| 6 pandoc | `grep -c '^= '` in typst output == chapter file count |
| 7 typst | no `unknown font` in stderr |
| 7 typst | `pdffonts` shows a mono family |
| 8 review | page count matches expectation |

Five greps. They would have caught both.

---

## Smaller gaps

| Gap | Detail |
|-----|--------|
| `thai-wordbreak.py` incomplete | The skill's code block omits the `if __name__ == "__main__"` block. Copied as printed, it is a no-op. |
| Fenced blocks not protected | The script preserves inline `` `code` `` but has no fence state. Thai text inside a fenced block gets ZWSP injected. |
| `magick` missing | The cover bg-match trick needs ImageMagick. Not installed on mba. |
| `timeout` missing | Used in no skill directly, but macOS has no `timeout`. Use `gtimeout`. |
| `sed -i ''` is BSD-only | Correct for macOS, breaks on GNU. |
| Doc/reality drift | The documented book dir has `book.yaml` and a `Makefile`; the one built here has neither, and used a `cover.html` instead of a typst cover block. |
| Cheatsheet mining loses signal | Commands are deduped into a set, so frequency and order are gone. It answers "which commands", never "how often" or "in what sequence". |
| Cheatsheet template signature | The template ends with a hardcoded `arra-oracle-v3` signature line. Leica must replace it, not paste it. |

---

## What I take forward

The skill is a good pipeline with a broken success signal. Exit code 0 means "typst did
not crash", not "the book is correct". This is the same lesson already in memory as
[[api_roundtrip_proves_storage_not_rendering]] - a clean round trip proves storage, not
rendering - and it repeated here at a larger scale, on a book that was published.

The published book should be re-rendered before it is cited or reshared. That is Un's
call, not mine.
