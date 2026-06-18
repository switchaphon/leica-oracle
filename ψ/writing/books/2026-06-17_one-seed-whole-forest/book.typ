#set page(paper: "a4", margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
#set text(font: "Sarabun", size: 12pt, lang: "th")
#set heading(numbering: none)
#set par(leading: 1.6em, justify: false, first-line-indent: 0em)
#set block(spacing: 2.5em)

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  set text(size: 20pt, weight: "bold")
  v(2em); it; v(1em)
}

#show heading.where(level: 2): it => {
  set text(size: 14pt, weight: "bold")
  v(1em); it; v(0.5em)
}

#show raw.where(block: true): it => {
  set text(font: "Fira Code", size: 9pt)
  block(fill: rgb("#f6f8fa"), stroke: 0.5pt + luma(200),
    inset: 14pt, radius: 4pt, width: 100%, it)
}

#show raw.where(block: false): it => {
  box(fill: rgb("#f0f0f0"), inset: (x: 3pt, y: 1.5pt), radius: 2pt,
    text(font: "Fira Code", size: 9pt, fill: rgb("#36454f"), it))
}

#show strong: it => {
  text(weight: "bold", fill: rgb("#1a1a2e"), it)
}

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
