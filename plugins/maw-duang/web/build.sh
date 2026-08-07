#!/usr/bin/env bash
# Bundle the engine for the browser and inline it into the page. No CDN, no fetch —
# an Artifact runs under a CSP that blocks every external host, and a Thai chart
# should not phone home with someone's birth data anyway.
set -euo pipefail
cd "$(dirname "$0")"
bun build browser-entry.ts --target=browser --minify --outfile=/tmp/duang.bundle.js
python3 - <<'PY'
b = open("/tmp/duang.bundle.js", encoding="utf-8").read()
t = open("index.template.html", encoding="utf-8").read()
open("index.html","w",encoding="utf-8").write(t.replace("/*BUNDLE*/", b))
print("built web/index.html")
PY
