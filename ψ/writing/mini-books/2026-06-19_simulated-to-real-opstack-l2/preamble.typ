// ===== oracle-booklet typst preamble v2 — learned from complete-book (200pp proven) =====
//   cat preamble.typ body.typ > full.typ
//   typst compile --font-path /System/Library/Fonts --font-path /System/Library/AssetsV2 --font-path ~/Library/Fonts full.typ out.pdf
// (Sarabun lives under AssetsV2 on macOS — include it or the cover/body may fall back.)
// Proven layout (11.5pt / leading 1.5em / block 2em) → ~14 pages for ~3000 words + code.
// v2 changelog: larger fonts, more spacing, rule lines on headings, fill: white after cover.

// Font applies document-wide — set it BEFORE the cover so the cover uses it too (gotcha #5/#6).
#set text(font: ("Sarabun", "IBM Plex Sans Thai Looped"), lang: "th")

// --- Cover page (NO page number) — Cover B: dark + architecture diagram ---
#set page(paper: "a4", margin: 0cm, fill: rgb("#1a1a2e"))
#place(top, rect(width: 100%, height: 6pt, fill: gradient.linear(rgb("#e74c3c"), rgb("#f39c12"), rgb("#e74c3c"))))
#v(6em)
#align(center, {
  box(
    width: 70%,
    stroke: 1pt + rgb("#334466"),
    radius: 8pt,
    inset: 16pt,
    fill: rgb("#141428"),
    {
      align(center, text(size: 10pt, fill: rgb("#667799"))[L1 · Sepolia Testnet · chainId 11155111])
      v(1em)
      align(center, text(size: 10pt, fill: rgb("#556688"))[─────── ▼ derive ▼ ───────])
      v(1em)
      align(center, text(size: 13pt, weight: "bold", fill: rgb("#3498db"))[op-node (CL) — libp2p])
      v(0.6em)
      align(center, text(size: 10pt, fill: rgb("#556688"))[─── Engine API ───])
      v(0.6em)
      align(center, text(size: 13pt, weight: "bold", fill: rgb("#2ecc71"))[op-geth (EL) — chainId 20260619])
    }
  )
})
#v(3em)
#align(center, text(size: 46pt, weight: "bold", fill: white)[จำลอง])
#v(0.3em)
#align(center, text(size: 52pt, weight: "bold", fill: rgb("#e74c3c"))[≠])
#v(0.3em)
#align(center, text(size: 46pt, weight: "bold", fill: white)[จริง])
#v(2em)
#align(center, text(size: 13pt, fill: rgb("#8899bb"))[
  จาก simulated chain ถึง OP Stack L2 บน Sepolia — ถูก correct 3 รอบ
])
#v(1fr)
#align(center, text(size: 13pt, weight: "bold", fill: rgb("#e74c3c"))[
  Leica 🐱 (AI, ไม่ใช่คน) — จาก Un
])
#v(0.6em)
#align(center, text(size: 10pt, fill: rgb("#556688"))[19 มิถุนายน 2026 · Workshop-06 · 17 หน้า])
#v(3em)
#place(bottom, rect(width: 100%, height: 6pt, fill: gradient.linear(rgb("#e74c3c"), rgb("#f39c12"), rgb("#e74c3c"))))

// --- Content pages (numbered, start at 1) ---
// GOTCHA #12: ALWAYS reset fill + margin here (dark cover uses margin:0cm + dark fill — both leak!)
#set page(numbering: "1", fill: white, margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
#counter(page).update(1)
#pagebreak()

// Typography — from complete-book (proven readable at 200pp, crew-master 2026-06-18)
#set text(size: 11.5pt)
#set par(leading: 1.5em, justify: false)
#set block(spacing: 2em)

// L2 = section heading with colored rule line (visual hierarchy from complete-book)
#show heading.where(level: 2): it => {
  v(1.2em)
  line(length: 100%, stroke: 1.5pt + rgb("#c0392b"))
  v(0.6em)
  set text(size: 18pt, weight: "bold", fill: rgb("#1a1a2e"))
  it
  v(0.8em)
}

// L3 = subsection
#show heading.where(level: 3): it => {
  v(0.8em)
  set text(size: 13pt, weight: "bold", fill: rgb("#2c3e50"))
  it
  v(0.4em)
}

// Code blocks — readable size (9pt not 8.5pt), more padding
#show raw.where(block: true): it => block(fill: rgb("#f6f8fa"), stroke: 0.5pt + luma(200), inset: 12pt, radius: 4pt, width: 100%, text(font: "Fira Code", size: 9pt, it))

// Inline code — readable
#show raw.where(block: false): it => box(fill: rgb("#f0f0f0"), inset: (x: 3pt, y: 1.5pt), radius: 2pt, text(font: "Fira Code", size: 9pt, fill: rgb("#36454f"), it))

// Bold — distinct
#show strong: it => text(weight: "bold", fill: rgb("#1a1a2e"), it)

// Tables — more padding (10pt not 8pt)
#set table(stroke: 0.5pt + luma(180), fill: (_, r) => if r == 0 { rgb("#2c3e50") } else if calc.odd(r) { rgb("#f8f9fa") } else { white }, inset: 10pt)
// GOTCHA #4 — body cells LEFT, header centered (never ship a center-aligned body table):
#show table.cell: it => { set text(size: 10pt); if it.y == 0 { align(center, text(fill: white, weight: "bold", it)) } else { align(left, it) } }
