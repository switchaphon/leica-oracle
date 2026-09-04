#!/usr/bin/env python3
"""build.py - inject snapshot.json + provinces.json into page.template.html."""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
tpl  = open(os.path.join(here, "page.template.html"), encoding="utf-8").read()
snap = json.load(open(sys.argv[1] if len(sys.argv) > 1
                      else os.path.expanduser("~/hii-data/snapshot.json"), encoding="utf-8"))
geo  = json.load(open(os.path.join(here, "provinces.json"), encoding="utf-8"))

# Radar is optional: if radar.py has not run, the page ships without the layer
# rather than failing the build. initRadar() leaves its control hidden.
rpath = os.path.expanduser("~/hii-data/radar.json")
rad = json.load(open(rpath, encoding="utf-8")) if os.path.exists(rpath) else {}

lpath = os.path.expanduser("~/hii-data/layers.json")
lay = json.load(open(lpath, encoding="utf-8")) if os.path.exists(lpath) else {}

out = (tpl.replace("__DATA__", json.dumps(snap, ensure_ascii=False, separators=(",", ":")))
          .replace("__GEO__",  json.dumps(geo,  ensure_ascii=False, separators=(",", ":")))
          .replace("__RADAR__", json.dumps(rad, ensure_ascii=False, separators=(",", ":")))
          .replace("__LAYERS__", json.dumps(lay, ensure_ascii=False, separators=(",", ":"))))
assert not any(t in out for t in ("__DATA__", "__GEO__", "__RADAR__", "__LAYERS__"))
dst = os.path.join(here, "waterviz.html")
open(dst, "w", encoding="utf-8").write(out)
print(f"{dst}  {os.path.getsize(dst)/1024:.0f} KB")
