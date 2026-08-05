#!/usr/bin/env python3
"""
jira-adf — post real ADF (tables, headings, code blocks) to Jira Cloud.

Why this exists
---------------
The `jira-rpro` / `jira-pops` MCP servers wrap every string into flat ADF paragraphs.
`jira_add_comment` takes only `body: string`; there is no channel through which rich
content can ever be passed. This tool talks to /rest/api/3/ directly and builds the ADF
document itself.

It adds NO new credential. It reuses the same JIRA_{RPRO,POPS}_API_TOKEN that the MCP
servers already authenticate with, read from the environment only — never an argument,
never printed.

The two instances stay separated exactly as before: --jira selects which set of env vars
is used, and a project-key guard refuses to post RPRO-* to the pops instance or vice versa.

Usage
-----
  jira-adf.py --jira rpro --check
  jira-adf.py --jira rpro --issue RPRO-15475 --comment note.md            # dry run
  jira-adf.py --jira rpro --issue RPRO-15475 --comment note.md --post
  jira-adf.py --jira pops --issue POPS-278 --description spec.md --post
  cat note.md | jira-adf.py --jira rpro --issue RPRO-15475 --comment - --post
  jira-adf.py --jira rpro --issue RPRO-15475 --comment doc.json --adf --post

Dry run is the default. Nothing is written to Jira without --post.

Verification note: a 201 and a matching read-back prove STORAGE, not RENDERING. This tool
prints the browse URL after posting — open it and look. Only eyes verify layout.
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

INSTANCES = {
    "rpro": ("JIRA_RPRO_BASE_URL", "JIRA_RPRO_EMAIL", "JIRA_RPRO_API_TOKEN"),
    "pops": ("JIRA_POPS_BASE_URL", "JIRA_POPS_EMAIL", "JIRA_POPS_API_TOKEN"),
}

# Known project keys per instance. A key listed here may only go to its own instance.
# Keys not listed anywhere are allowed with a warning (new projects appear over time).
KEY_OWNER = {"RPRO": "rpro", "POPS": "pops", "PP": "pops"}


# ─────────────────────────── markdown → ADF ───────────────────────────

INLINE_RE = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<lhref>[^)\s]+)\)"
    r"|\*\*(?P<strong>[^*]+)\*\*"
    r"|(?<![\w*])\*(?P<em>[^*\n]+)\*(?![\w*])"
    r"|(?<![\w_])_(?P<em2>[^_\n]+)_(?![\w_])"
)


def _text(s, marks=None):
    """ADF text node. ADF rejects empty text nodes, so callers must skip empties."""
    node = {"type": "text", "text": s}
    if marks:
        node["marks"] = marks
    return node


def inline(src):
    """Parse inline markup into a list of ADF inline nodes."""
    out, pos = [], 0
    for m in INLINE_RE.finditer(src):
        if m.start() > pos:
            out.append(_text(src[pos:m.start()]))
        if m.group("code"):
            out.append(_text(m.group("code"), [{"type": "code"}]))
        elif m.group("ltext"):
            out.append(_text(m.group("ltext"),
                             [{"type": "link", "attrs": {"href": m.group("lhref")}}]))
        elif m.group("strong"):
            out.append(_text(m.group("strong"), [{"type": "strong"}]))
        elif m.group("em"):
            out.append(_text(m.group("em"), [{"type": "em"}]))
        elif m.group("em2"):
            out.append(_text(m.group("em2"), [{"type": "em"}]))
        pos = m.end()
    if pos < len(src):
        out.append(_text(src[pos:]))
    return [n for n in out if n.get("text")]


def para(src):
    content = inline(src)
    return {"type": "paragraph", "content": content} if content else {"type": "paragraph"}


def _cell(kind, src):
    return {"type": kind, "attrs": {}, "content": [para(src.strip())]}


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_table_sep(line):
    s = line.strip()
    return bool(s) and set(s) <= set("|-: \t") and "-" in s and "|" in s


def markdown_to_adf(text):
    """Convert a practical subset of Markdown to an ADF document."""
    lines = text.replace("\r\n", "\n").split("\n")
    content, i = [], 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # blank
        if not stripped:
            i += 1
            continue

        # fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or None
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            node = {"type": "codeBlock", "attrs": {}}
            if lang:
                node["attrs"]["language"] = lang
            body = "\n".join(buf)
            if body:
                node["content"] = [_text(body)]
            content.append(node)
            continue

        # horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            content.append({"type": "rule"})
            i += 1
            continue

        # heading
        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            content.append({
                "type": "heading",
                "attrs": {"level": len(m.group(1))},
                "content": inline(m.group(2).strip()),
            })
            i += 1
            continue

        # table: a pipe row followed by a separator row
        if "|" in stripped and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            header = _split_row(lines[i])
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_split_row(lines[i]))
                i += 1
            width = max([len(header)] + [len(r) for r in rows]) if rows else len(header)

            def pad(cells):
                return cells + [""] * (width - len(cells))

            table = {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": [{
                    "type": "tableRow",
                    "content": [_cell("tableHeader", c) for c in pad(header)],
                }],
            }
            for r in rows:
                table["content"].append({
                    "type": "tableRow",
                    "content": [_cell("tableCell", c) for c in pad(r)],
                })
            content.append(table)
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            content.append({"type": "blockquote", "content": [para(" ".join(buf).strip())]})
            continue

        # lists
        bullet = re.match(r"[-*+]\s+(.*)", stripped)
        ordered = re.match(r"\d+[.)]\s+(.*)", stripped)
        if bullet or ordered:
            kind = "bulletList" if bullet else "orderedList"
            pat = r"[-*+]\s+(.*)" if bullet else r"\d+[.)]\s+(.*)"
            items = []
            while i < len(lines):
                mm = re.match(pat, lines[i].strip())
                if not mm:
                    break
                items.append({"type": "listItem", "content": [para(mm.group(1).strip())]})
                i += 1
            content.append({"type": kind, "content": items})
            continue

        # paragraph — consecutive non-blank lines, joined with hard breaks
        buf = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"(#{1,6}\s|```|>|[-*+]\s|\d+[.)]\s)", lines[i].strip()):
            if "|" in lines[i] and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
                break
            buf.append(lines[i].strip())
            i += 1
        nodes = []
        for n, part in enumerate(buf):
            if n:
                nodes.append({"type": "hardBreak"})
            nodes.extend(inline(part))
        content.append({"type": "paragraph", "content": nodes} if nodes else {"type": "paragraph"})

    if not content:
        content = [{"type": "paragraph"}]
    return {"type": "doc", "version": 1, "content": content}


# ─────────────────────────── jira transport ───────────────────────────

def creds(instance):
    base_v, email_v, token_v = INSTANCES[instance]
    base, email, token = (os.environ.get(v, "").strip() for v in (base_v, email_v, token_v))
    missing = [v for v, x in ((base_v, base), (email_v, email), (token_v, token)) if not x]
    if missing:
        sys.exit(f"error: {', '.join(missing)} not set in the environment.\n"
                 f"       These live in ~/.zshenv. Run from a shell that sources it.")
    return base.rstrip("/"), email, token


def request(method, url, email, token, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:800]
        return e.code, {"_error": body}
    except urllib.error.URLError as e:
        sys.exit(f"error: cannot reach Jira — {e.reason}")


def guard_key(issue, instance):
    prefix = issue.split("-")[0].upper()
    owner = KEY_OWNER.get(prefix)
    if owner is None:
        print(f"warning: project key {prefix!r} is not in the known map; "
              f"sending to --jira {instance} as instructed.", file=sys.stderr)
    elif owner != instance:
        sys.exit(f"refused: {issue} belongs to the {owner!r} instance, "
                 f"but --jira {instance} was given. The two Jiras stay separate.")


def read_source(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r") as fh:
        return fh.read()


def main():
    ap = argparse.ArgumentParser(
        description="Post rich ADF (tables, headings, code) to Jira Cloud.")
    ap.add_argument("--jira", required=True, choices=sorted(INSTANCES),
                    help="which Jira instance — selects its own credentials")
    ap.add_argument("--issue", help="issue key, e.g. RPRO-15475")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--comment", metavar="FILE", help="markdown file to post as a comment ('-' for stdin)")
    src.add_argument("--description", metavar="FILE", help="markdown file to set as the description")
    ap.add_argument("--adf", action="store_true",
                    help="input is already an ADF document in JSON, pass through untouched")
    ap.add_argument("--post", action="store_true",
                    help="actually write to Jira (default is a dry run)")
    ap.add_argument("--check", action="store_true",
                    help="verify credentials read-only, write nothing")
    args = ap.parse_args()

    base, email, token = creds(args.jira)

    if args.check:
        status, body = request("GET", f"{base}/rest/api/3/myself", email, token)
        if status == 200:
            print(f"ok  {args.jira}: authenticated as {body.get('displayName')} "
                  f"<{body.get('emailAddress')}> at {base}")
            return 0
        print(f"FAIL {args.jira}: HTTP {status} at {base}\n{body.get('_error','')}",
              file=sys.stderr)
        return 1

    if not args.issue or not (args.comment or args.description):
        ap.error("--issue and one of --comment/--description are required (or use --check)")

    guard_key(args.issue, args.jira)

    raw = read_source(args.comment or args.description)
    if args.adf:
        doc = json.loads(raw)
        if doc.get("type") != "doc":
            sys.exit("error: --adf given but the JSON is not an ADF document (type != 'doc')")
    else:
        doc = markdown_to_adf(raw)

    kinds = {}
    for n in doc.get("content", []):
        kinds[n["type"]] = kinds.get(n["type"], 0) + 1
    summary = " · ".join(f"{v}× {k}" for k, v in sorted(kinds.items()))

    if not args.post:
        print(json.dumps(doc, indent=2, ensure_ascii=False))
        print(f"\n--- DRY RUN — nothing sent. {summary}", file=sys.stderr)
        print(f"--- target: {args.issue} on {args.jira} ({base})", file=sys.stderr)
        print("--- add --post to write it.", file=sys.stderr)
        return 0

    if args.comment:
        status, body = request("POST", f"{base}/rest/api/3/issue/{args.issue}/comment",
                               email, token, {"body": doc})
        ok = status in (200, 201)
        where = f"comment {body.get('id')}" if ok else ""
    else:
        status, body = request("PUT", f"{base}/rest/api/3/issue/{args.issue}",
                               email, token, {"fields": {"description": doc}})
        ok = status in (200, 204)
        where = "description"

    if not ok:
        print(f"FAILED: HTTP {status}\n{body.get('_error','')}", file=sys.stderr)
        return 1

    print(f"posted {where} to {args.issue} ({summary})")
    print(f"VERIFY BY EYE: {base}/browse/{args.issue}")
    print("A 2xx proves storage, not rendering. Open it and look before calling it done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
