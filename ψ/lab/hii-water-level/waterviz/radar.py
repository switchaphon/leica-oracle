#!/usr/bin/env python3
"""
radar.py - bake a rain radar loop into a JSON blob the page can embed.

  python3 radar.py --out ~/hii-data/radar.json

Why bake rather than fetch live: a published artifact runs under a CSP that
blocks images and XHR from any non-allowlisted host, silently. Pointing the page
at tilecache.rainviewer.com works when opened from disk and renders nothing once
published, with no console error to explain it. Baked tiles are data: URIs, which
the CSP does allow - and the whole page is already a snapshot, so a snapshot of
the radar is consistent with how everything else on it works.

Source: RainViewer (https://www.rainviewer.com), the same feed twa.thaiwater.net
paints for its own radar layer. Free tier, no key. Attribution is required and
the page carries it.

The Thai radar images on twa.thaiwater.net are a different product - 40 station
pictures in each radar's own polar projection, not georeferenced tiles - so they
cannot be overlaid on a Mercator map without warping each one. Not attempted.
"""

import argparse
import base64
import concurrent.futures
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

INDEX = "https://api.rainviewer.com/public/weather-maps.json"
TZ7 = timezone(timedelta(hours=7))

# The station extent, padded out so the radar does not stop at the edge of the
# markers. Kept here rather than derived from the snapshot so radar.py can run
# without one.
LAT0, LAT1 = 13.531, 19.638
LON0, LON1 = 98.201, 101.353
PAD = 0.25

# RainViewer serves radar up to z=7. Above that every tile comes back HTTP 200
# as one identical PNG reading "Zoom Level Not Supported".
#
# That placeholder is why z=8 first measured *smaller* than z=7 (32 KB against
# 92 KB): 24 copies of the same small error image compress better than 12 real
# ones. Size looked like evidence of efficient encoding and was evidence of
# failure. The tiles were only caught by rendering them and reading the words.
# assert_real_tiles() below refuses a frame whose tiles are all identical AND
# too large to be empty, so raising ZOOM fails loudly - while a genuinely
# rain-free frame, which is ALSO all-identical, still bakes.
ZOOM = 7
MAX_ZOOM = 7

# RainViewer tile path: /{size}/{z}/{x}/{y}/{colour}/{smooth}_{snow}.png
# colour 4 is the scheme with a transparent no-echo background.
COLOUR = 4
OPTIONS = "1_1"


def tile_xy(lat, lon, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    la = math.radians(lat)
    y = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n
    return x, y


def grid(z):
    x0, y0 = tile_xy(LAT1 + PAD, LON0 - PAD, z)
    x1, y1 = tile_xy(LAT0 - PAD, LON1 + PAD, z)
    xs = list(range(int(math.floor(x0)), int(math.floor(x1)) + 1))
    ys = list(range(int(math.floor(y0)), int(math.floor(y1)) + 1))
    return xs, ys


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "leica-waterviz/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# A fully transparent RainViewer tile is ~334 bytes. The "Zoom Level Not
# Supported" placeholder is a rendered text image and runs into the kilobytes.
# Size is what separates them; identity does not.
BLANK_TILE_MAX = 800


def assert_real_tiles(pngs, zoom, when):
    """Refuse a frame whose tiles are all identical AND all large.

    The first version of this refused any frame whose tiles were all identical,
    on the reasoning that "real radar over a 3-degree box is never byte-identical
    tile to tile". That reasoning is wrong, and measurably so: over a rain-free
    box every tile is the same 334-byte fully-transparent PNG. Verified
    2026-09-05, 12 of 12 tiles identical at z=7.

    So the original guard fires on exactly the condition it was built to allow -
    a working service reporting no rain - and in the Thai dry season that is most
    frames. It would have aborted every bake from November to April, and
    refresh.sh would have logged "keeping the previous radar.json" while the page
    served an ever-older loop. An anti-false-positive guard that becomes a
    seasonal false-positive generator.

    Identity alone cannot tell "placeholder" from "no rain". Size can, because
    the placeholder carries rendered text and a transparent tile carries nothing.
    """
    if len(pngs) > 1 and len(set(pngs)) == 1:
        # base64 inflates by 4/3; compare against the decoded size
        decoded = len(pngs[0]) * 3 // 4
        if decoded > BLANK_TILE_MAX:
            raise SystemExit(
                f"radar: every tile at z={zoom} is identical and {decoded} bytes "
                f"- too big to be an empty tile, so the service is returning a "
                f"placeholder, not radar (frame {when}). "
                f"RainViewer serves up to z={MAX_ZOOM}."
            )
        print(f"  frame {when}: no echo anywhere in the box "
              f"({decoded} B/tile) - kept, this is weather not failure",
              file=sys.stderr)


def build(nframes, zoom):
    if zoom > MAX_ZOOM:
        raise SystemExit(f"radar: z={zoom} is above RainViewer's maximum z={MAX_ZOOM}")
    meta = json.loads(fetch(INDEX).decode())
    host = meta["host"]
    past = meta["radar"]["past"]
    frames = past[-nframes:] if nframes else past

    xs, ys = grid(zoom)
    n = 2 ** zoom
    span = 256.0 / n           # tile width in the page's mercator units

    # The page draws in Web Mercator with the world 256 units wide, centred on 0,
    # which is exactly tile z=0. So a tile's top-left is X*256/2^z - 128.
    cells = [{"x": round(x * span - 128, 6), "y": round(y * span - 128, 6)}
             for x in xs for y in ys]

    def one(job):
        i, (x, y, url) = job
        try:
            return i, base64.b64encode(fetch(url)).decode()
        except Exception as exc:
            print(f"  tile {x},{y} failed: {exc}", file=sys.stderr)
            return i, None

    out_frames = []
    for fr in frames:
        jobs = [(i, (x, y, f"{host}{fr['path']}/256/{zoom}/{x}/{y}/{COLOUR}/{OPTIONS}.png"))
                for i, (x, y) in enumerate((x, y) for x in xs for y in ys)]
        with concurrent.futures.ThreadPoolExecutor(12) as ex:
            got = dict(ex.map(one, jobs))
        if any(v is None for v in got.values()):
            print(f"  frame {fr['time']} incomplete, skipped", file=sys.stderr)
            continue
        pngs = [got[i] for i in range(len(cells))]
        assert_real_tiles(pngs, zoom, fr["time"])
        out_frames.append({
            "t": fr["time"],
            "label": datetime.fromtimestamp(fr["time"], TZ7).strftime("%H:%M"),
            "date": datetime.fromtimestamp(fr["time"], TZ7).strftime("%Y-%m-%d"),
            "png": pngs,
        })

    if not out_frames:
        raise SystemExit("no complete radar frames - refusing to write an empty loop")

    return {
        "zoom": zoom,
        "span": round(span, 6),
        "cells": cells,
        "frames": out_frames,
        "fetchedAt": datetime.now(TZ7).strftime("%Y-%m-%d %H:%M"),
        "source": "RainViewer",
        "attribution": "เรดาร์ฝน: RainViewer (rainviewer.com)",
        "note": ("ภาพเรดาร์ฝัง ณ เวลาที่ build ไม่ใช่ live - "
                 "หน้านี้เป็น snapshot ทั้งหน้า"),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.expanduser("~/hii-data/radar.json"))
    p.add_argument("--frames", type=int, default=10,
                   help="how many past frames to bake (0 = all available)")
    p.add_argument("--zoom", type=int, default=ZOOM)
    a = p.parse_args()

    data = build(a.frames, a.zoom)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    kb = os.path.getsize(a.out) / 1024
    print(f"{len(data['frames'])} frames x {len(data['cells'])} tiles "
          f"@ z{data['zoom']} -> {a.out} ({kb:.0f} KB)")
    print(f"  window {data['frames'][0]['label']} to {data['frames'][-1]['label']} "
          f"({data['frames'][-1]['date']} +07)")


if __name__ == "__main__":
    main()
