#!/usr/bin/env python3
"""
layers.py - bake the rain-gauge and CCTV layers into a JSON blob for the page.

  python3 layers.py --out ~/hii-data/layers.json

Source is twa-api-public.thaiwater.net, a *different* API from the
api-v3.thaiwater.net that supplies the water levels: different host, different
auth, different code scheme - but largely the SAME stations. 768 of twa's 780
water level stations sit on api-v3 coordinates to within 0.1 m, so only the rain
gauges, cameras and radar here are genuinely new. See ψ/learn/thaiwater/twa/.

Both layers are baked rather than fetched, for the same reason as radar.py: a
published artifact's CSP blocks XHR and images from non-allowlisted hosts with
no visible error.

CCTV needs a word of warning. The API reports isActive: true on all 85 cameras
and that flag means nothing - nationwide, only 10 of 57 hostnames resolve at
all. So this script probes each camera at build time and records what actually
answered, rather than passing the vendor's flag through to the page.

Read the states precisely. 'nodns' means the NAME does not resolve, not that
the camera is dead: dyndns.org withdrew its free tier, so a lapsed account
explains it and the hardware may still be filming. And 'live' counts cameras
that returned a JPEG; the EXIF check on top of that is a lower bound, because a
camera serving a current frame without EXIF fails it while being fine.

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
import hashlib
import json
import os
import re
import socket
import sys
import time
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

# Layer 4's poll gap. MEASURED, not chosen: the EGAT feeds refresh at exactly
# 60 s (EXIF stepping 23:15:12 / 23:16:12 / 23:17:12 with the bytes changing in
# step, 2026-09-04), so 90 s carries a margin. That measurement is from ONE
# camera family, and the refresh period is a property of each source.
#
# This single global value is safe ONLY because the layer-4 verdict is one-sided
# (see probe(): identical bytes return "unknown", never "frozen"). A source
# refreshing slower than 90 s therefore comes back UNKNOWN - honest, not wrong.
# The two decisions are coupled: if anyone ever makes identical bytes mean
# FROZEN, this constant becomes a false-positive generator for every source
# slower than the one camera it was measured on. Change neither alone.
GAP_SECONDS = 90


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


def probe(cam, timeout=8, second_poll=True):
    """Ask the camera itself whether it is alive. isActive is not evidence.

    Four layers, and only the last one cannot be lied to.

      1  DNS resolves          catches a lapsed hostname
      2  HTTP 200 + JPEG magic catches a dead service
      3  time inside the file  catches a live service serving an old picture
      4  bytes changed         catches everything layer 3 cannot see

    Layers 1-3 all rest on something the source declares. EXIF, an overlay, a
    storage tag: each is a claim about when the frame is from, and a frozen
    source can restate any of them. Layer 4 asks a different question - did
    anything change between two polls - which involves no timestamp at all, so
    there is nothing to misstate.

    Layer 4 has one precondition, and getting it wrong inverts the result.
    THE GAP MUST EXCEED THE SOURCE'S REFRESH PERIOD. These endpoints are not
    live MJPEG; they are still JPEGs on a web server rewritten on a cycle, so
    two polls inside one cycle return identical bytes from a perfectly healthy
    camera. Measured on เขื่อนภูมิพล 2026-09-04:

        t=0s   exif 23:15:12  hash A
        t=5s   exif 23:15:12  hash A     unchanged
        t=15s  exif 23:15:12  hash A     unchanged
        t=30s  exif 23:16:12  hash B     changed
        t=90s  exif 23:17:12  hash C     changed

    Exactly 60 s. A 1.5 s gap - the first thing I wrote - reported FROZEN for
    two cameras whose EXIF was advancing every minute. The "sensor noise makes
    consecutive frames differ" argument holds for a live stream and not for a
    cached file, so the period is a property of each source and has to be
    measured, not assumed. GAP_SECONDS below is set from that measurement.

    Credit rpro-ent-oracle for the layer, who pointed out the tool was already
    in this repo aimed at radar tiles; the precondition is what running it
    against real cameras added.
    """
    url = (cam["u"] or "") + (cam["fn"] or "")
    host = urllib.parse.urlparse(url).hostname
    if not host:
        return "nourl", None, None, None
    try:
        socket.gethostbyname(host)
    except Exception:
        return "nodns", None, None, None
    try:
        # Every camera in this feed is plain http. Nothing here weakens TLS: if
        # one ever moves to https it gets verified normally, and a bad
        # certificate should fail the probe rather than be waved through.
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            blob = r.read(400_000)
    except Exception:
        return "noanswer", None, None, None

    if blob[:2] != b"\xff\xd8":
        return "notimage", None, None, None
    # Axis cameras carry the capture time in EXIF. A valid JPEG is not proof the
    # picture is current: one camera in this feed serves a 2024 frame under a
    # perfectly good HTTP 200, so record the stamp and let the page show it.
    m = re.search(rb"(20\d\d:\d\d:\d\d \d\d:\d\d:\d\d)", blob[:6000])
    stamp = m.group(1).decode() if m else None

    if not second_poll:
        return "live", stamp, blob, None

    # Layer 4. The gap has to clear one full refresh cycle of the source.
    time.sleep(GAP_SECONDS)
    try:
        req2 = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                    "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req2, timeout=timeout) as r2:
            blob2 = r2.read(400_000)
        frozen = hashlib.sha256(blob).digest() == hashlib.sha256(blob2).digest()
    except Exception:
        frozen = None          # could not ask twice; do not claim either way
    # Layer 4 is ONE-SIDED. Bytes differing proves the source produced something
    # new, with no knowledge of its period needed. Bytes matching means frozen OR
    # polled inside one refresh cycle, and those are indistinguishable from here -
    # so it reports "unknown", never "frozen". Credit rpro-ent-oracle: the first
    # version of this returned "frozen" and would have libelled any camera whose
    # refresh is slower than GAP_SECONDS.
    if frozen is None:
        return "unknown", stamp, blob, None
    return ("unknown" if frozen else "live"), stamp, blob, frozen


def cctv_layer(do_probe=True, second_poll=True):
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
            results = list(ex.map(lambda c: probe(c, second_poll=second_poll), cams))
        spent = 0
        # Baked in the order the cameras are listed, not by size. Sorting by
        # size would quietly favour whichever frame happens to compress well,
        # which is not a reason to prefer one working camera over another.
        for cam, (state, stamp, blob, frozen) in zip(cams, results):
            cam["st"] = state
            if stamp:
                cam["ts"] = stamp
            if frozen is not None:
                cam["changed"] = not frozen
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
    p.add_argument("--no-second-poll", action="store_true",
                   help="skip layer 4, which costs GAP_SECONDS of wall clock")
    a = p.parse_args()

    rain = rain_layer()
    cams = cctv_layer(not a.no_probe, second_poll=not a.no_second_poll)

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
