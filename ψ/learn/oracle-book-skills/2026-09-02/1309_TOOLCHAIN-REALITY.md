# Toolchain reality on mba

Substituted for the `--deep` TESTING lens: these skills have no test suite, so the
equivalent question is "will the pipeline actually run here, end to end?"

All checks run 2026-09-02 13:09 +07 on mba (darwin 25.6.0, arm64).

## Status

| Tool | Needed for | Status |
|------|-----------|--------|
| `typst` | step 7 render, cover render | OK - 0.15.0 |
| `pandoc` | step 6 md to typst | OK - 3.10 |
| `uvx` / `uv` | PyThaiNLP runner | OK |
| `python3` | wordbreak, session mining | OK - homebrew |
| PyThaiNLP `newmm` | step 5 word break | OK via uvx, first run downloads |
| `pdfinfo` | cover page-count guard | OK (poppler) |
| `pdftoppm` | eyeball renders, social crops | OK (poppler) |
| `pdffonts` | verify embedded fonts | OK (poppler) |
| `gh` | step 10 publish | OK |
| **`magick`** | cover bg-match trick | **MISSING** |
| Font: Sarabun | body text | OK |
| Font: Didot | cover wordmark | OK |
| **Font: Fira Code** | all code blocks | **MISSING** |

typst sees 398 font families. Neither `Fira Code` nor any other Fira family is among
them.

## Reproduce these checks

```bash
for t in typst pandoc uvx uv python3 magick pdfinfo pdftoppm pdffonts gh; do
  command -v "$t" >/dev/null && echo "OK   $t" || echo "MISS $t"
done

typst --version
pandoc --version | head -1
typst fonts | grep -iE "sarabun|didot|^fira" | sort -u
typst fonts | grep -iE "mono|code" | sort -u        # what mono you DO have

uvx --from pythainlp python3 -c \
  "from pythainlp.tokenize import word_tokenize; print(word_tokenize('ทดสอบ', engine='newmm'))"
```

Note: `timeout` does not exist on macOS. Use `gtimeout` (coreutils) or drop it.

## Available monospace families

```
JetBrains Mono      <- recommended replacement, verified
Menlo
SF NS Mono
DejaVu Sans Mono
PT Mono
Andale Mono
Courier / Courier New
Ubuntu Mono / Ubuntu Sans Mono
```

## The positive control

A negative result is worthless without proof the test can detect anything. Both checks
below were run before trusting the "Fira Code is missing" conclusion:

1. **The warning fires.** Compiling a file that requests `Fira Code`:
   ```
   warning: unknown font family: fira code
   ```
   Exit code: **0**. The build "succeeds".

2. **`pdffonts` can see fonts.** The same test PDF reported
   `QENGLA+Sarabun-Regular` and `XHGGLN+LibertinusSerif-Regular`. So a blank mono
   result means genuinely no mono, not a broken detector.

3. **The replacement produces no warning and embeds.** Recompiling with
   `JetBrains Mono`: no warning, exit 0, `MVBNVB+JetBrainsMono-Regular` embedded,
   ASCII tree aligned in the rendered PNG.

## Two fixes to run before the next book

```bash
brew install imagemagick                    # unblocks cover bg-match
brew install --cask font-fira-code          # or edit book.typ to JetBrains Mono
```

Neither is applied yet - both are outward-facing installs and were left for Un to call.

## Cost shape of a full run

Not measured here, but the skill's own record for "The Oracle Pattern" (15 chapters,
200+ pages):

- 15 Sonnet agents drafting
- 14 Sonnet agents writing files
- 3 Sonnet review agents
- 2 rounds of title brainstorm at 10 perspectives x 3 judges
- 10 iterations of typst styling

That is roughly 100 agent invocations for one book. The deterministic steps (5, 6, 7)
are free and should never be delegated.
