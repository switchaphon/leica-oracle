# Code snippets - the runnable parts, corrected against this machine

Everything below was executed or compiled on mba, 2026-09-02. Where the skill text
differs from what actually works here, the working version is given and the difference
is called out.

## 1. book.typ - corrected

The skill ships `font: "Fira Code"` for both raw rules. **Fira Code is not installed
here** (`typst fonts | grep -ci '^fira'` returns 0). Typst warns and exits 0, so the
build looks fine and the code blocks silently fall back to a proportional serif.

Verified replacement: `JetBrains Mono` (present, compiles with no warning, embeds
correctly, ASCII trees align).

```typst
// Page setup
#set page(paper: "a4", margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
#set text(font: "Sarabun", size: 12pt, lang: "th")
#set heading(numbering: none)
#set par(leading: 1.6em, justify: false, first-line-indent: 0em)
#set block(spacing: 2.5em)

// Chapter headings - page break before
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 20pt, weight: "bold")
  v(2em); it; v(1em)
}

#show heading.where(level: 2): it => {
  set text(size: 14pt, weight: "bold")
  v(1em); it; v(0.5em)
}

// Code blocks - CHANGED from "Fira Code" (absent on mba)
#show raw.where(block: true): it => {
  set text(font: "JetBrains Mono", size: 9pt)
  block(fill: rgb("#f6f8fa"), stroke: 0.5pt + luma(200),
    inset: 14pt, radius: 4pt, width: 100%, it)
}

// Inline code - CHANGED from "Fira Code"
#show raw.where(block: false): it => {
  box(fill: rgb("#f0f0f0"), inset: (x: 3pt, y: 1.5pt), radius: 2pt,
    text(font: "JetBrains Mono", size: 9pt, fill: rgb("#36454f"), it))
}

#show strong: it => { text(weight: "bold", fill: rgb("#1a1a2e"), it) }

#show quote.where(block: true): it => {
  block(fill: rgb("#f0f4f8"), stroke: (left: 3pt + rgb("#3498db")),
    inset: (left: 16pt, right: 12pt, top: 10pt, bottom: 10pt),
    radius: (right: 4pt), it)
}

#set table(
  stroke: 0.5pt + luma(180),
  fill: (_, row) => if row == 0 { rgb("#2c3e50") }
    else if calc.odd(row) { rgb("#f8f9fa") } else { white },
)
#show table.cell: it => {
  set text(size: 10pt); set align(left)
  if it.y == 0 { set text(fill: white, weight: "bold"); it } else { it }
}

#outline(title: "สารบัญ", depth: 1)
```

Mono families actually available here, in preference order:
`JetBrains Mono`, `Menlo`, `SF NS Mono`, `DejaVu Sans Mono`, `PT Mono`, `Andale Mono`.

To install the original instead: `brew install --cask font-fira-code`.

## 2. thai-wordbreak.py - complete

The skill's code block stops after `insert_zwsp()`. Copied as printed it defines a
function and does nothing. The `__main__` block below is required and is present in the
shipped copy at `ψ/writing/books/2026-06-17_one-seed-whole-forest/thai-wordbreak.py`.

```python
#!/usr/bin/env python3
"""Insert ZWSP at Thai word boundaries for proper line breaking in typst."""
import sys, re
from pythainlp.tokenize import word_tokenize

ZWSP = "​"

def has_thai(text):
    return bool(re.search(r'[฀-๿]', text))

def insert_zwsp(text):
    if not has_thai(text):
        return text
    parts = re.split(r'(`[^`]+`)', text)   # preserve inline code
    result = []
    for part in parts:
        if part.startswith('`'):
            result.append(part)
        elif has_thai(part):
            segments = re.split(r'([฀-๿]+)', part)
            for seg in segments:
                if has_thai(seg):
                    result.append(ZWSP.join(word_tokenize(seg, engine="newmm")))
                else:
                    result.append(seg)
        else:
            result.append(part)
    return ''.join(result)

if __name__ == "__main__":                 # MISSING from the skill text
    for fpath in sys.argv[1:]:
        with open(fpath, 'r') as f:
            for line in f:
                print(insert_zwsp(line), end='')
```

Note the script preserves inline code spans but **not** fenced code blocks - it works
line by line with no fence state. Fenced blocks pass through only because their content
is usually ASCII and `has_thai()` returns False. A Thai comment inside a fenced block
will get ZWSP injected.

Verified working:

```bash
uvx --from pythainlp python3 -c \
  "from pythainlp.tokenize import word_tokenize; \
   print(word_tokenize('ทดสอบการตัดคำภาษาไทย', engine='newmm'))"
# ['ทดสอบ', 'การ', 'ตัด', 'คำ', 'ภาษาไทย']
```

First run downloads pythainlp; subsequent runs install from cache in ~6 ms.

## 3. Compile chain

```bash
# 5. word break every chapter in order into one stream
for f in 0*.md 1*.md; do
  uvx --from pythainlp python3 thai-wordbreak.py "$f" >> /tmp/book-zwsp.md
done

# 6. markdown -> typst markup
pandoc /tmp/book-zwsp.md -o book-typst.typ -t typst
sed -i '' 's/#horizontalrule/#line(length: 100%)/g' book-typst.typ
cat book.typ book-typst.typ > book-full.typ

# 7. render
typst compile book-full.typ book.pdf
```

`sed -i ''` is the BSD form - correct for macOS, would need `sed -i` on GNU.

**Always read the warnings.** `typst compile` returns 0 on unknown fonts.

## 4. Verify the render actually worked

The pipeline has no verification step. These three do the job:

```bash
# any font families missing? (exit code will NOT tell you)
typst compile book-full.typ book.pdf 2>&1 | grep -i "unknown font" && echo "FONT FALLBACK"

# is a monospace font actually embedded?
pdffonts book.pdf | grep -iE "mono|code|menlo|courier" || echo "NO MONO EMBEDDED"

# page count and eyeballing
pdfinfo book.pdf | grep -i pages
pdftoppm -f 13 -l 13 -r 130 -png -singlefile book.pdf /tmp/p13   # then read the PNG
```

## 5. Session mining (oracle-cheatsheet step 1)

```bash
ORACLE_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
ENCODED_PWD=$(echo "$ORACLE_ROOT" | sed 's|^/|-|; s|[/.]|-|g')
PROJECT_DIR="$HOME/.claude/projects/${ENCODED_PWD}"
LATEST_JSONL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
```

Then the extractor walks assistant messages for `tool_use` blocks named `Bash` and
takes the first segment before `&&` or `|`, capped at 80 chars. It dedupes into a set,
so ordering and frequency are both lost - it tells you *which* commands, never *how
often* or *in what sequence*.

## 6. Cover render loop (oracle-book-cover step 3)

```bash
typst compile --format png \
  --font-path /System/Library/Fonts \
  --font-path /System/Library/Fonts/Supplemental \
  --font-path "$HOME/Library/Fonts" cover-cand.typ "cand-{p}.png"
```

Two pages out means the content overflowed - shrink until one page.

The `--font-path` flags are needed for `Didot` (the elegant wordmark trick). Didot is
present here. The bg-match trick needs ImageMagick:

```bash
magick img.png -format '%[hex:p{2,2}]' info:
```

**`magick` is not installed on mba** - `brew install imagemagick` first, or sample the
corner colour another way.

## 7. Social crops

```bash
# 1080x1080 and 1080x1350 exported from the cover, as separate assets
pdftoppm -f 1 -l 1 -r 300 -png -singlefile book.pdf cover
```
The prior book here produced `cover-1x1.png` and `cover-4x5.png` this way.
