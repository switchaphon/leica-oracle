# Quick reference - which skill, when

## Picking the right one

The family has more writing skills than these three. Full decision table, merged from
all three skills' own "related" sections plus what is installed here:

| Want | Skill | Output |
|------|-------|--------|
| 1-page command reference from this session | `/oracle-cheatsheet` | 1 md file |
| Short guide, 3-5 chapters | `/oracle-write-book` | md |
| 12-15 page proof-dense booklet, one session | `/oracle-booklet` | PDF |
| Looser short book, no proof bar | `/oracle-write-mini-book` | PDF |
| Full book, 10-20 chapters, 200+ pages | `/oracle-write-complete-book` | PDF + repo |
| 50K-word book | `/oracle-write-endgame` | PDF |
| A cover for any of the above | `/oracle-book-cover` | typst block + PNGs |
| Build-it-yourself manual (vol 2) | `/oracle-write-techbook` | PDF |

`/oracle-book-cover` is never used alone - it edits an existing `book.typ`.

## Triggers

**oracle-write-complete-book**: "เขียนหนังสือ", "write book", "complete book",
"เขียนเล่มยาว", or any request for a full book with PDF output.
Explicitly does NOT trigger for short guides, cheatsheets, or single docs.

**oracle-cheatsheet**: "cheatsheet", "cheat sheet", "สูตรโกง", "รวมคำสั่ง",
"command reference".

**oracle-book-cover**: "book cover", "ปกหนังสือ", "ทำปก", "redesign cover",
"social cover".

## Output paths

```
ψ/writing/books/<slug>/                       complete-book working dir
ψ/writing/books/YYYY-MM-DD_<slug>-OUTLINE.md  the outline (step 1)
ψ/writing/cheatsheets/YYYY-MM-DD_<topic>.md   cheatsheet
```

Existing here: `ψ/writing/books/2026-06-17_one-seed-whole-forest`,
`ψ/writing/cheatsheets/2026-06-19_workshop-06-opstack-l2-sepolia.md`.

Cheatsheets are **append/update**, not rewrite, if one already exists for the topic.

## Chapter budget (complete-book)

| Part | Words | Job |
|------|-------|-----|
| Hook | 200-300 | pull the reader in |
| Body | 2,500-3,000 | 3-5 subtopics |
| Code/diagram | 300-500 | 2-3 blocks |
| Close | 200-300 | lesson + hook to next |
| **Total** | **3,000-4,000** | 10-15 min read |

Three-part default: เรื่องเล่า (overview) / Technical (deep dive) / Design and Vision.

## Typography rules

| Rule | Value | Why |
|------|-------|-----|
| Body | Sarabun 12pt proportional | Thai looped font, readable |
| Code | 9pt mono | see the font trap below |
| Line height | 1.6em | Thai ascenders and descenders |
| Block spacing | 2.5em | paragraph gap must exceed line gap |
| Justify | false | Thai has no word spaces to stretch |
| Margin | 3cm sides, 2.5cm top/bottom | ~65 chars per line |
| TOC depth | 1 | chapter titles only |
| Numbering | none | no 3.1.2 nesting |

**Font trap**: the shipped config asks for `Fira Code`, which is absent on mba. Use
`JetBrains Mono` or run `brew install --cask font-fira-code`. Details in
`1309_TRAPS-AND-GAPS.md`.

## kien-thai 7 frames (used in every drafting prompt)

```
f1  topic-comment, not SVO
f2  condition first (พอ...ก็...)
f3  spaces, not full stops
f4  close with particles (ด้วย / แล้ว / เลย / ต่างหาก)
f5  zero anaphora + demonstratives
f6  ก็ as rhythm
f7  pivot with a question or แต่
```

## Cheatsheet house style

1. Title + 1-line tagline
2. Icon sections (🔧 📨 🔍 🌐 📋 🔁 ⚡ ⚠️)
3. Code blocks that paste and run - real values from the session, no placeholders
4. A `| ทำอะไร | คำสั่ง |` shortcut table at the end
5. A `| trap | วิธีเลี่ยง |` table from what actually went wrong
6. No long prose, no closing summary - it ends at the trap table
7. An env/config section gathering all vars in one place
8. 🤖 signature (Rule 6)

Topic selection: take it from the latest context. Do not ask.

## Cover: the non-negotiables

1. Cover only. Chapters, content and page count untouched - verify with `pdfinfo`.
2. IP gate first (step 0), never after: find the LICENSE, confirm the asset is really
   tracked in the repo (`git ls-files --error-unmatch`), check trademark, attach credit.
3. Eyeball every render. Read the PNG. Never assume it looks good.
4. Deterministic tools do the work - typst and magick, not agents.
5. Human approves anything outward-facing (commit, push, post).
6. Sign the cover as AI (Rule 6).

## Global checklist before publishing

- Every chapter has real proof (code path, issue number, trace log)
- DNA woven into narrative, not listed
- Failures included honestly
- kien-thai frames throughout
- No recap at the close - forward-looking
- Code blocks paste and run
- Author is the oracle name, not a human (Rule 6)
- Private repos marked clearly
- Agents wrote files; they did not return text
