#!/usr/bin/env python3
"""
layers.py - bake the rain-gauge and CCTV layers into a JSON blob for the page.

  python3 layers.py --out ~/hii-data/layers.json

Source is twa-api-public.thaiwater.net, a *different* API from the
api-v3.thaiwater.net that supplies the water levels: different host, different
auth, different station sets. See ψ/learn/thaiwater/twa/ for the survey.

Both layers are baked rather than fetched, for the same reason as radar.py: a
published artifact's CSP blocks XHR and images from non-allowlisted hosts with
no visible error.

CCTV needs a word of warning. The API reports isActive: true on all 85 cameras
and that flag means nothing - nationwide, only 10 of 57 hostnames resolve at
all. So this script probes each camera at build time and records what actually
answered, rather than passing the vendor's flag through to the page.

Camera frames ARE embedded, for the cameras that answer - a modal on the page
shows the picture without sending the reader to a third-party host. The CSP on a
published artifact blocks an <img> pointing at a camera, so a live <img> would
render on disk and silently show nothing once published; the frame has to be
baked like the radar.

Only the handful that actually respond get baked, and IMAGE_BUDGET caps the
total, because there is no image library here to downscale with and the frames
run 200-500 KB each.
"""

import argparse
import base64
import concurrent.futures
import json
import os
import re
import socket
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://twa-api-public.thaiwater.net"
KEY = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x"
TZ7 = timezone(timedelta(hours=7))

LAT0, LAT1 = 13.531, 19.638
LON0, LON1 = 98.201, 101.353

RAIN_WINDOW = 1440  # cumulative minutes; the token is c<minutes>, 1440 = 24 h

# Total raw bytes of camera frames to embed. Frames are baked whole (no image
# library here to downscale with), so this is the only thing keeping four
# 500 KB JPEGs from doubling the page.
IMAGE_BUDGET = 2_200_000


def api(path):
    req = urllib.request.Request(API + path,
                                 headers={"x-api-key": KEY, "Accept-Language": "th"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def features(payload):
    """MAP routes are keyed by province code, so len(data) counts provinces."""
    d = payload.get("data", {})
    if isinstance(d, list):
        return d
    return [f for fc in d.values() if isinstance(fc, dict) and "features" in fc
            for f in fc["features"]]


def inbox(f):
    try:
        lon, lat = f["geometry"]["coordinates"][:2]
    except Exception:
        return None
    if LAT0 <= lat <= LAT1 and LON0 <= lon <= LON1:
        return lat, lon
    return None


def rain_layer():
    rows = features(api(f"/v2/rainfall/rainfall_c{RAIN_WINDOW}"))
    out = []
    for f in rows:
        c = inbox(f)
        if not c:
            continue
        p = f["properties"]
        v = p.get("measureValue")
        if v is None:
            continue
        st = p.get("station") or {}
        geo = p.get("geoCode") or {}
        out.append({
            "la": round(c[0], 5), "lo": round(c[1], 5),
            "n": st.get("station") or "-",
            "v": round(float(v), 1),
            "t": (p.get("measureAt") or "")[11:16],
            "p": geo.get("province") or "",
            "a": ((p.get("agency") or {}).get("agency")
                  if isinstance(p.get("agency"), dict) else None) or "",
        })
    out.sort(key=lambda r: -r["v"])
    return out


def probe(cam, timeout=8):
    """Ask the camera itself whether it is alive. isActive is not evidence."""
    url = (cam["u"] or "") + (cam["fn"] or "")
    host = urllib.parse.urlparse(url).hostname
    if not host:
        return "nourl", None, None
    try:
        socket.gethostbyname(host)
    except Exception:
        return "nodns", None, None
    try:
        # Every camera in this feed is plain http. Nothing here weakens TLS: if
        # one ever moves to https it gets verified normally, and a bad
        # certificate should fail the probe rather than be waved through.
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            blob = r.read(400_000)
    except Exception:
        return "noanswer", None, None

    if blob[:2] != b"\xff\xd8":
        return "notimage", None, None
    # Axis cameras carry the capture time in EXIF. A valid JPEG is not proof the
    # picture is current: one camera in this feed serves a 2024 frame under a
    # perfectly good HTTP 200, so record the stamp and let the page show it.
    m = re.search(rb"(20\d\d:\d\d:\d\d \d\d:\d\d:\d\d)", blob[:6000])
    return "live", (m.group(1).decode() if m else None), blob


def cctv_layer(do_probe=True):
    rows = features(api("/v2/cctv"))
    cams = []
    for f in rows:
        c = inbox(f)
        if not c:
            continue
        p = f["properties"]
        cams.append({
            "la": round(c[0], 5), "lo": round(c[1], 5),
            "n": p.get("cctvTitle") or "-",
            "u": p.get("cctvUrl"), "fn": p.get("cctvFilename"),
            "ag": ((p.get("agency") or {}).get("agency")
                   if isinstance(p.get("agency"), dict) else None) or "",
        })
    if do_probe:
        with concurrent.futures.ThreadPoolExecutor(16) as ex:
            results = list(ex.map(probe, cams))
        spent = 0
        # Baked in the order the cameras are listed, not by size. Sorting by
        # size would quietly favour whichever frame happens to compress well,
        # which is not a reason to prefer one working camera over another.
        for cam, (state, stamp, blob) in zip(cams, results):
            cam["st"] = state
            if stamp:
                cam["ts"] = stamp
            if blob and spent + len(blob) <= IMAGE_BUDGET:
                cam["img"] = base64.b64encode(blob).decode()
                spent += len(blob)
            elif blob:
                cam["imgskip"] = "over budget"
        print(f"  embedded {spent/1024:.0f} KB of camera frames "
              f"(budget {IMAGE_BUDGET/1024:.0f} KB)", file=sys.stderr)
    for cam in cams:
        cam["url"] = (cam.pop("u") or "") + (cam.pop("fn") or "")
    return cams


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.expanduser("~/hii-data/layers.json"))
    p.add_argument("--no-probe", action="store_true",
                   help="skip the camera liveness probe (faster, less honest)")
    a = p.parse_args()

    rain = rain_layer()
    cams = cctv_layer(not a.no_probe)

    data = {
        "fetchedAt": datetime.now(TZ7).strftime("%Y-%m-%d %H:%M"),
        "rainWindow": RAIN_WINDOW,
        "rain": rain,
        "cctv": cams,
        "source": "twa-api-public.thaiwater.net",
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    live = sum(1 for c in cams if c.get("st") == "live")
    print(f"rain {len(rain)} gauges (max {rain[0]['v'] if rain else 0} mm), "
          f"cctv {len(cams)} in extent, {live} answered with a picture "
          f"-> {a.out} ({os.path.getsize(a.out)/1024:.0f} KB)")
    if cams and not a.no_probe:
        from collections import Counter
        print("  camera states:", dict(Counter(c.get("st") for c in cams)))


if __name__ == "__main__":
    main()
