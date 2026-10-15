# Architecture - the three book skills as one pipeline

Learned 2026-09-02 13:09 +07 by Leica. Source: three SKILL.md files, byte-identical
to the copies already installed in `~/.claude/skills/`.

## What these three actually are

They are not three independent tools. They are one publishing pipeline cut into three
pieces along the lines of *who decides what*:

| Skill | Owns | Decides |
|-------|------|---------|
| `oracle-write-complete-book` | the whole 11-step flow, content | structure, chapters, prose |
| `oracle-book-cover` | step 7 only (the cover block) | art, IP risk, visual hook |
| `oracle-cheatsheet` | nothing in the book | a separate 1-page artifact |

`oracle-cheatsheet` is the odd one out. It shares no code and no output path with the
other two. It landed in the same batch because all three mine the same raw material -
the session JSONL - not because they compose.

## The composition point

`oracle-write-complete-book` names `oracle-book-cover` in its "Relationship to Other
Skills" table as the replacement for doing the cover by hand. `oracle-book-cover`
names `/oracle-write-complete-book` in its Related section. The handshake is
deliberate and mutual, and it is narrow:

```
oracle-write-complete-book  Step 0..6   (mine -> outline -> draft -> wordbreak -> compile)
                            Step 7      -> oracle-book-cover  (cover block ONLY)
                            Step 8..10  (review -> iterate -> publish)
```

The contract between them is a single typst block. `oracle-book-cover`'s hard rule 1
is "cover only, never touch chapters", enforced by a page-count check:

```bash
pdfinfo book.pdf | grep -i pages   # must equal the pre-cover count
git diff --name-only               # must show only book.typ + art + pdf
```

That is the whole interface. No shared config, no shared state.

## The 11 steps and what each really costs

```
Step 0   Mine session          dig.py + gh issue view + traces      cheap, mandatory
Step 1   Outline               YAML per chapter                     cheap, mandatory
Step 2   Prism review          5 lenses on the outline              cheap
Step 3   Title brainstorm      Workflow: 10 perspectives x 3 judges 33 agents, expensive
Step 4   Parallel draft        1 Sonnet agent per chapter           N agents, the bulk
Step 5   Thai word break       PyThaiNLP newmm, ZWSP insertion      deterministic
Step 6   Compile               pandoc md -> typst                   deterministic
Step 7   Render                typst compile                        deterministic
Step 8   Review                3 Sonnet agents                      3 agents
Step 9   Iterate               fix, re-render, read the PDF         manual, eyes
Step 10  Publish               gh repo create + release             human gate
```

Steps 5, 6, 7 are deterministic - no agent should touch them. Steps 3, 4, 8 are the
only ones that justify fan-out. That split is the load-bearing design idea: agents
write prose, tools do typesetting.

## The one architectural rule that matters most

> Agents MUST write files, NOT return text.

Stated as CRITICAL in step 4 and repeated in the anti-patterns list. The reason is
context, not tidiness: 15 chapters at 3,500 words each returned as tool output would
bury the orchestrator. Each agent gets told:

```
Write to: <book-dir>/NN-slug.md
Return only: "wrote NN-slug.md - X words"
```

One line back per agent. This is the same discipline that makes the pipeline survive a
200-page book in a single session.

## Directory shape

```
ψ/writing/books/<slug>/
├── book.typ            styling config, hand-written
├── book.yaml           pandoc metadata
├── Makefile            make pdf / make latex
├── thai-wordbreak.py   ZWSP inserter
├── 00-frontmatter.md
├── 01-...md            one file per chapter, one agent per file
└── NN-...md
```

Verified against the one book already built here,
`ψ/writing/books/2026-06-17_one-seed-whole-forest` (10 chapters, 58 pages, 776 KB).
That build deviated: it used a `cover.html` rather than a typst cover block, and it
carries no `book.yaml` or `Makefile`. So the shipped shape is a subset of the
documented shape.

## Where the design is weakest

The pipeline treats `typst compile` exit code 0 as success. It is not. Typst emits
`warning: unknown font family` and still exits 0, so a missing font produces a clean
build and a broken book. See `1309_TRAPS-AND-GAPS.md` - this defect is present in the
one book already published from this machine.
