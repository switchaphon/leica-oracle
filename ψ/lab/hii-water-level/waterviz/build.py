#!/usr/bin/env python3
"""build.py - inject snapshot.json + provinces.json into page.template.html."""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
tpl  = open(os.path.join(here, "page.template.html"), encoding="utf-8").read()
snap = json.load(open(sys.argv[1] if len(sys.argv) > 1
                      else os.path.expanduser("~/hii-data/snapshot.json"), encoding="utf-8"))
geo  = json.load(open(os.path.join(here, "provinces.json"), encoding="utf-8"))
out = (tpl.replace("__DATA__", json.dumps(snap, ensure_ascii=False, separators=(",", ":")))
          .replace("__GEO__",  json.dumps(geo,  ensure_ascii=False, separators=(",", ":"))))
assert "__DATA__" not in out and "__GEO__" not in out
dst = os.path.join(here, "waterviz.html")
open(dst, "w", encoding="utf-8").write(out)
print(f"{dst}  {os.path.getsize(dst)/1024:.0f} KB")
