#!/usr/bin/env python3
"""
build-case-study.py - render CASE-STUDY.md into CASE-STUDY.html.

The HTML used to be hand-authored alongside the markdown. They drifted: the
markdown grew from 6 traps to 17 while the page kept claiming 6, including a
proof that had since been retracted. One source now, rendered.

  python3 build-case-study.py            # -> CASE-STUDY.html next to the .md
  python3 build-case-study.py --check     # exit 1 if the html is out of date
"""

import html as _html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "CASE-STUDY.md")
DST = os.path.join(HERE, "CASE-STUDY.html")

CSS = """
:root{
  --ground:#F6F9F9; --surface:#FFFFFF; --sunk:#EEF3F3;
  --ink:#0F1E20; --ink-2:#455A5C; --ink-3:#4E6A6D;
  --line:#D9E4E3; --line-2:#EAF0EF;
  --accent:#07626F; --accent-soft:#DCEDEF;
  --alert:#9E3B33; --alert-soft:#F7E4E2;
  --ok:#256B5B;
  --shadow:0 1px 2px rgba(15,30,32,.05), 0 10px 30px rgba(15,30,32,.05);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#070F12; --surface:#0E1B1F; --sunk:#132429;
    --ink:#E8F1F2; --ink-2:#B0C4C6; --ink-3:#8CA1A4;
    --line:#1E353A; --line-2:#16292E;
    --accent:#57C6D4; --accent-soft:#0E2E35;
    --alert:#E58074; --alert-soft:#2E1714;
    --ok:#5CBFA3;
    --shadow:0 1px 2px rgba(0,0,0,.45), 0 10px 30px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --ground:#070F12; --surface:#0E1B1F; --sunk:#132429;
  --ink:#E8F1F2; --ink-2:#B0C4C6; --ink-3:#8CA1A4;
  --line:#1E353A; --line-2:#16292E;
  --accent:#57C6D4; --accent-soft:#0E2E35;
  --alert:#E58074; --alert-soft:#2E1714;
  --ok:#5CBFA3;
  --shadow:0 1px 2px rgba(0,0,0,.45), 0 10px 30px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font-family:"IBM Plex Sans Thai","Noto Sans Thai","Sarabun",system-ui,-apple-system,sans-serif;
  font-size:15.5px;line-height:1.68;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 72px}
.col{max-width:72ch}
.mono,code,pre{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-variant-numeric:tabular-nums}

header.top{padding:52px 0 30px;border-bottom:2px solid var(--ink)}
.kicker{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);
  font-weight:600;margin-bottom:14px}
h1{margin:0;font-size:clamp(29px,4.4vw,44px);line-height:1.11;font-weight:600;
  letter-spacing:-.022em;text-wrap:balance;max-width:20ch}
.standfirst{margin:16px 0 0;font-size:17.5px;line-height:1.6;color:var(--ink-2);max-width:64ch}
.byline{display:flex;flex-wrap:wrap;gap:8px 26px;margin-top:24px;font-size:12.5px;color:var(--ink-3)}
.byline b{color:var(--ink-2);font-weight:500}
.links{margin:14px 0 0;font-size:13px}
.links a{font-weight:500}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:1px;
  background:var(--line);border:1px solid var(--line);margin:34px 0 4px;border-radius:10px;overflow:hidden}
.fig{background:var(--surface);padding:16px 18px 15px}
.fig b{display:block;font-size:27px;font-weight:600;line-height:1.1;letter-spacing:-.02em}
.fig span{display:block;font-size:11.5px;color:var(--ink-3);margin-top:5px;line-height:1.4}

section{padding-top:42px}
h2{margin:0 0 4px;font-size:12px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--accent)}
h3{margin:0 0 16px;font-size:clamp(21px,2.5vw,26px);font-weight:600;letter-spacing:-.014em;
  line-height:1.25;text-wrap:balance}
h4{margin:26px 0 8px;font-size:16.5px;font-weight:600;letter-spacing:-.005em}
p{margin:0 0 15px}
strong{font-weight:600;color:var(--ink)}
em{font-style:italic}
a{color:var(--accent)}
ul,ol{margin:0 0 15px;padding-left:22px}
li{margin-bottom:6px}
blockquote{margin:18px 0;padding:2px 0 2px 16px;border-left:3px solid var(--accent);color:var(--ink-2)}
blockquote p:last-child{margin-bottom:0}
code:not(pre code){font-size:.87em;background:var(--sunk);padding:1.5px 5px;border-radius:4px;
  border:1px solid var(--line-2);color:var(--ink)}

.tw{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{text-align:left;font-weight:600;font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-3);padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap;background:var(--sunk)}
td{padding:10px 14px;border-bottom:1px solid var(--line-2);vertical-align:top;color:var(--ink-2)}
tr:last-child td{border-bottom:none}
td:first-child{color:var(--ink)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}

pre{margin:18px 0;padding:15px 17px;background:var(--sunk);border:1px solid var(--line);
  border-radius:9px;overflow-x:auto;font-size:12.5px;line-height:1.62;color:var(--ink)}
pre code{background:none;border:none;padding:0}

.trap{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--alert);
  border-radius:0 10px 10px 0;padding:17px 21px 18px;box-shadow:var(--shadow);margin:16px 0}
.trap .tn{font-size:11px;color:var(--alert);letter-spacing:.06em;font-weight:600;
  font-family:"IBM Plex Mono",monospace}
.trap h4{margin:5px 0 10px;font-size:17.5px}
.trap > :last-child{margin-bottom:0}
.trap .tw{margin:14px 0 0}

footer{margin-top:52px;padding-top:22px;border-top:1px solid var(--line);color:var(--ink-3);
  font-size:12.5px;line-height:1.75}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

FIGS = [
    ("878,095", "readings in SQLite"),
    ("518", "stations, 8 basins"),
    (None, "silent-failure traps found"),   # None = counted from the markdown
    ("~$120", "API-equivalent token cost"),
]

WORDS = {
    6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven",
    12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen", 16: "Sixteen",
    17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty",
    21: "Twenty-one", 22: "Twenty-two", 23: "Twenty-three", 24: "Twenty-four",
    25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
}


def count_traps(md):
    """The number of traps is derived, never typed.

    This page once spent a day claiming six while the markdown held seventeen,
    because the count lived in the renderer and the traps lived in the source.
    It appeared in four places - h1, <title>, the figure strip and the meta
    description - so keeping them in step by hand was four chances to drift.
    """
    return len(re.findall(r"^### 3\.\d+\s", md, re.M))


def inline(t):
    """Markdown inline -> HTML. Code spans are extracted first so their
    contents are never treated as markup."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans)-1}\x00"

    t = re.sub(r"`([^`\n]+)`", stash, t)
    t = _html.escape(t, quote=False)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"(?<![\">=])(https?://[^\s<)]+)",
               r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"<code>\1</code>", t)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f"<code>{_html.escape(spans[int(m.group(1))], quote=False)}</code>", t)


NUMERIC = re.compile(r"^[\s\d.,%+\-x:/$()]*$")


def render_table(rows):
    head, body = rows[0], rows[2:]
    ncol = len(head)
    numeric = [all(NUMERIC.match(r[i]) and r[i].strip() for r in body if i < len(r))
               for i in range(ncol)]
    out = ['<div class="tw"><table>', "<thead><tr>"]
    for i, h in enumerate(head):
        out.append(f'<th{" class=\"n\"" if numeric[i] else ""}>{inline(h)}</th>')
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i in range(ncol):
            cell = r[i] if i < len(r) else ""
            out.append(f'<td{" class=\"n\"" if numeric[i] else ""}>{inline(cell)}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# The masthead composes these from the same lines, so rendering them again in
# the body prints the byline twice.
MASTHEAD_KEYS = ("Built", "By", "For", "Read as a page", "The dashboard itself")


def is_masthead_line(ln):
    return any(ln.startswith(f"**{k}**") for k in MASTHEAD_KEYS)


def convert(md):
    lines = md.split("\n")
    body, i = [], 0
    open_section = open_trap = open_col = False

    def close_col():
        nonlocal open_col
        if open_col:
            body.append("</div>")
            open_col = False

    def close_trap():
        nonlocal open_trap
        if open_trap:
            body.append("</div>")
            open_trap = False

    def close_section():
        nonlocal open_section
        close_trap(); close_col()
        if open_section:
            body.append("</section>")
            open_section = False

    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            close_col()
            body.append("<pre><code>" + _html.escape("\n".join(buf), quote=False) + "</code></pre>")
            i = j + 1
            continue

        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            close_col()
            if len(rows) >= 2:
                body.append(render_table(rows))
            continue

        if re.match(r"^#{1,4} ", ln):
            level = len(ln) - len(ln.lstrip("#"))
            text = ln[level:].strip()
            if level == 1:
                i += 1
                continue                       # the masthead carries the title
            if level == 2:
                close_section()
                m = re.match(r"^(\d+)\.\s*(.+)$", text)
                num, title = (m.group(1), m.group(2)) if m else ("", text)
                body.append("<section>")
                open_section = True
                body.append('<div class="col">')
                open_col = True
                if num:
                    body.append(f'<h2>{int(num):02d}</h2>')
                body.append(f"<h3>{inline(title)}</h3>")
            elif level == 3:
                close_trap()
                m = re.match(r"^3\.(\d+)\s+(.+)$", text)
                if m:                          # a trap gets its own card
                    close_col()
                    body.append('<div class="trap">')
                    open_trap = True
                    body.append(f'<div class="tn">TRAP {int(m.group(1)):02d}</div>')
                    body.append(f"<h4>{inline(m.group(2))}</h4>")
                else:
                    if not open_col:
                        body.append('<div class="col">'); open_col = True
                    body.append(f"<h4>{inline(text)}</h4>")
            else:
                if not (open_col or open_trap):
                    body.append('<div class="col">'); open_col = True
                body.append(f"<h4>{inline(text)}</h4>")
            i += 1
            continue

        if ln.strip() == "---":
            i += 1
            continue

        if re.match(r"^\s*[-*] ", ln) or re.match(r"^\s*\d+\. ", ln):
            ordered = bool(re.match(r"^\s*\d+\. ", ln))
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*] ", lines[i]) or re.match(r"^\s*\d+\. ", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])); i += 1
            if not (open_col or open_trap):
                body.append('<div class="col">'); open_col = True
            tag = "ol" if ordered else "ul"
            body.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue

        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip()); i += 1
            if not (open_col or open_trap):
                body.append('<div class="col">'); open_col = True
            body.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        if is_masthead_line(ln):
            i += 1
            continue

        if ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#{1,4} |\||```|>|\s*[-*] |\s*\d+\. |---\s*$)", lines[i]) \
                    and not is_masthead_line(lines[i]):
                buf.append(lines[i].strip()); i += 1
            if not (open_col or open_trap):
                body.append('<div class="col">'); open_col = True
            body.append(f"<p>{inline(' '.join(buf))}</p>")
            continue

        i += 1

    close_section()
    return "\n".join(body)


def build():
    md = open(SRC, encoding="utf-8").read()

    # the masthead is composed, not converted - it carries figures the prose does not
    meta = {}
    for k in ("Built", "By", "For"):
        m = re.search(rf"^\*\*{k}\*\*\s+(.+)$", md, re.M)
        if m:
            meta[k] = m.group(1)
    stand = ("One question - \"have we ever pulled from this URL?\" - became a running ingest "
             "for 518 telemetry stations across the Greater Chao Phraya, and then a second "
             "survey of a second API on a near-identical name. Every trap below produces "
             "output that looks correct.")

    n = count_traps(md)
    word = WORDS.get(n, str(n))

    figs = "".join(
        f'<div class="fig"><b class="mono">{n if v is None else v}</b>'
        f'<span>{lbl}</span></div>' for v, lbl in FIGS)
    byline = "".join(f"<span><b>{k}</b> {inline(v)}</span>" for k, v in meta.items())
    links = []
    for label in ("Read as a page", "The dashboard itself"):
        m = re.search(rf"^\*\*{re.escape(label)}\*\*\s+(\S+)", md, re.M)
        if m:
            links.append(f'<a href="{m.group(1)}" target="_blank" rel="noopener">{label}</a>')
    linkbar = f'<p class="links">{" &#183; ".join(links)}</p>' if links else ""

    head = f"""<header class="top">
  <div class="kicker">Field report / rpro-ent-oracle</div>
  <h1>{word} traps in Thailand's public water feed</h1>
  <p class="standfirst">{stand}</p>
  <div class="byline">{byline}</div>
  {linkbar}
  <div class="figs">{figs}</div>
</header>"""

    page = f"""<title>{word} Traps in Thailand's Water Feed</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
{head}
{convert(md)}
<footer>
  Generated from <span class="mono">CASE-STUDY.md</span> by <span class="mono">build-case-study.py</span> -
  the two used to be maintained separately and drifted, which is how this page spent a day claiming six traps
  while the markdown had grown to seventeen. The count is now derived from the source, not typed.<br><br>
  Written by Leica Oracle (AI, ไม่ใช่คน). Every number here was measured in-session; where something is
  unverified it says so.
</footer>
</div>"""

    offline = f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Field report on integrating Thailand's HII water telemetry across two separate ThaiWater APIs - {n} silent-failure traps, the ingest design, WCAG measurements, and cost.">
<meta name="author" content="Leica Oracle">
{page}
</body>
</html>
"""
    return page, offline


if __name__ == "__main__":
    page, offline = build()
    if "--check" in sys.argv:
        cur = open(DST, encoding="utf-8").read() if os.path.exists(DST) else ""
        if cur != offline:
            print("CASE-STUDY.html is out of date - run build-case-study.py", file=sys.stderr)
            sys.exit(1)
        print("CASE-STUDY.html is current")
    else:
        open(DST, "w", encoding="utf-8").write(offline)
        art = os.path.join(HERE, ".case-study.artifact.html")
        open(art, "w", encoding="utf-8").write(page)
        print(f"{DST}  {os.path.getsize(DST)/1024:.0f} KB")
        print(f"{art}  {os.path.getsize(art)/1024:.0f} KB  (artifact body, no doctype wrapper)")
