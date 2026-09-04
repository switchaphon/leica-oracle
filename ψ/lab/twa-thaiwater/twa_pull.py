#!/usr/bin/env python3
"""
twa_pull.py - pull rainfall, water level, CCTV and rain radar from twa.thaiwater.net

Everything here was verified against the live API on 2026-09-04. No auth beyond
the anonymous x-api-key that the site's own JS bundle ships.

Usage:
    python3 twa_pull.py rainfall [1440|4320|7200|10080|21600]
    python3 twa_pull.py waterlevel
    python3 twa_pull.py cctv
    python3 twa_pull.py radar-sites
    python3 twa_pull.py radar-image <radarType> [outfile.jpg]
    python3 twa_pull.py radar-tiles                # RainViewer frame list
    python3 twa_pull.py all --out DIR              # dump everything as JSON
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://twa-api-public.thaiwater.net"
IMG = "https://platform.thaiwater.net/api/v1/public/media/view"

# Anonymous key, hardcoded in the site bundle's axios request interceptor.
# Sent as x-api-key whenever no logged-in bearer token exists.
KEY = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x"

TZ7 = timezone(timedelta(hours=7))

# Rainfall accumulation windows. The token is cumulative MINUTES, not a label:
# c1440 = 24h. Anything below a day (c15..c720) returns 400 - it is not served.
RAIN_WINDOWS = {
    1440: "24 hours",
    4320: "3 days",
    7200: "5 days",
    10080: "7 days",
    21600: "15 days",
}


def get(path, params=None, raw=False):
    url = API + path
    if params:
        url += ("&" if "?" in path else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"x-api-key": KEY, "Accept-Language": "th"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = r.read()
    return body if raw else json.loads(body)


def features(payload):
    """MAP endpoints return {data: {<provinceCode>: FeatureCollection}}.

    The top-level key count is provinces, not records - /v2/cctv looks like
    44 rows until you flatten it and find 85 cameras.
    """
    data = payload.get("data", {})
    if isinstance(data, list):
        return data
    out = []
    for value in data.values():
        if isinstance(value, dict) and "features" in value:
            out.extend(value["features"])
    return out


def rainfall(minutes=1440):
    return features(get(f"/v2/rainfall/rainfall_c{minutes}"))


def waterlevel():
    return features(get("/v2/waterlevel"))


def cctv():
    return features(get("/v2/cctv"))


def paged(path, page_size=1000):
    """List endpoints need BOTH pagination params or they error / ignore you.

    pagination[page] alone -> 1004 INVALID_DATA. pageSize alone -> silently
    ignored, you get page 1 of 10 forever. pageSize=-1 works on /v2/agency but
    returns 0 rows on /v2/cctv/list, so pass a real number.
    """
    return get(path, {"pagination[page]": 1, "pagination[pageSize]": page_size})


def radar_sites(agency_ids=(13, 10, 19), day=None):
    """TMD (13), Bangkok (10) and HII (19) radar image records.

    startDate/endDate are MANDATORY - without them the endpoint returns
    500 {"code":1006,"message":"无操作权限"}, which reads like a permissions
    failure but is really a missing-parameter failure.
    """
    day = day or datetime.now(TZ7).strftime("%Y-%m-%d")
    out = []
    for agency in agency_ids:
        payload = get(
            "/data/platform/v1/public/media",
            {
                "mediaTypeId": 30,
                "startDate": f"{day} 00:00",
                "endDate": f"{day} 23:59",
                "limit": -1,
                "latest": "true",
                "agencyId": agency,
            },
        )
        for row in payload.get("data", []):
            attrs = row["attributes"]
            attrs["agencyId"] = agency
            out.append(attrs)
    return out


def radar_image(radar_type, outfile=None):
    """Fetch one radar frame as bytes.

    isStaticFile must be false here. The site's only IMAGE_URL builder hardcodes
    isStaticFile=true, which is correct for waterlevel cross-sections and 404s
    for every radar frame.
    """
    for site in radar_sites():
        if site.get("radarType") == radar_type and site.get("mediaPath"):
            url = f"{IMG}?isStaticFile=false&mediaPath={urllib.parse.quote(site['mediaPath'], safe='')}"
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"x-api-key": KEY}), timeout=90
            ) as r:
                blob = r.read()
            if outfile:
                with open(outfile, "wb") as fh:
                    fh.write(blob)
            return blob, site
    raise SystemExit(f"no live frame for radar site {radar_type!r}")


def radar_tiles():
    """RainViewer - the animated radar the map actually paints.

    Tile template: {host}{path}/{size}/{z}/{x}/{y}/{colour}/{smooth}_{snow}.png
    The site uses size 256, colour 2. Frames land every 10 minutes.
    """
    with urllib.request.urlopen(
        "https://api.rainviewer.com/public/weather-maps.json", timeout=60
    ) as r:
        data = json.load(r)
    frames = []
    for frame in data["radar"]["past"] + data["radar"].get("nowcast", []):
        frames.append(
            {
                "time_local": datetime.fromtimestamp(frame["time"], TZ7).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "template": f"{data['host']}{frame['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
            }
        )
    return frames


def frame_time(site):
    """Recover the true local frame time for a radar record.

    Do NOT trust mediaDatetime. It is inconsistent across sites:
      - most (ubn240, omkoi, ...) carry the UTC wall-clock but tag it +07:00,
        so a frame 20 minutes old reads as 7 hours old
      - rasisalai carries the local INGEST time, not the frame time at all

    The filename is the one honest clock: every producer embeds the frame time
    in UTC as YYYYMMDDHHMM. Parse that and add 7 hours.
    """
    import re

    m = re.search(r"(20\d{6})[-_]?(\d{4})", site.get("filename") or "")
    if not m:
        return None
    utc = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")
    return (utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == "rainfall":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
        rows = rainfall(minutes)
        print(f"{len(rows)} stations, {RAIN_WINDOWS.get(minutes, minutes)} accumulation")
        rows.sort(key=lambda f: f["properties"].get("measureValue") or 0, reverse=True)
        for f in rows[:8]:
            p = f["properties"]
            print(
                f"  {p.get('measureValue')!s:>7} mm  {p['measureAt'][11:16]}  "
                f"{p['station']['station']}  ({p['geoCode'].get('province')})"
            )

    elif cmd == "waterlevel":
        rows = waterlevel()
        print(f"{len(rows)} water level stations")
        over = [f for f in rows if (f["properties"].get("diffWlBank") or 1) <= 0]
        print(f"{len(over)} currently at or over bank")
        for f in rows[:8]:
            p = f["properties"]
            print(
                f"  msl {p.get('waterlevelMsl')!s:>8}  bank {p.get('diffWlBank')!s:>7}  "
                f"{p['waterlevelDatetime'][11:16]}  {p['station']['station']}"
            )

    elif cmd == "cctv":
        rows = cctv()
        live = [f for f in rows if f["properties"].get("cctvUrl")]
        print(f"{len(rows)} cameras registered, {len(live)} with a URL")
        print(
            "  NOTE isActive is true on all of them and means nothing. Measured "
            "2026-09-04:\n"
            "  57 hostnames, only 10 resolve (every dyndns.org one is NXDOMAIN), "
            "8 return\n"
            "  a JPEG, 4 have EXIF matching now. Check EXIF datetime before "
            "trusting a frame."
        )
        for f in live[:8]:
            p = f["properties"]
            print(f"  {p['cctvTitle']}  ->  {p['cctvUrl']}{p.get('cctvFilename') or ''}")

    elif cmd == "radar-sites":
        sites = radar_sites()
        live = [s for s in sites if s.get("mediaDatetime")]
        print(f"{len(sites)} radar sites, {len(live)} with a frame today")
        print(f"{'site':<12} {'mediaDatetime (unreliable)':<28} true local frame time")
        for s in live:
            print(
                f"  {s['radarType']:<12} {s['mediaDatetime']:<28} "
                f"{frame_time(s) or '?'}"
            )

    elif cmd == "radar-image":
        site = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else f"{site}.jpg"
        blob, meta = radar_image(site, out)
        print(f"{len(blob)} bytes -> {out}   ({meta['radarName']})")

    elif cmd == "radar-tiles":
        for f in radar_tiles():
            print(f"  {f['time_local']}  {f['template']}")

    elif cmd == "all":
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "twa-dump"
        os.makedirs(out, exist_ok=True)
        jobs = {
            "rainfall_24h": lambda: rainfall(1440),
            "rainfall_7d": lambda: rainfall(10080),
            "waterlevel": waterlevel,
            "waterlevel_canal": lambda: features(get("/v2/waterlevel/canal")),
            "waterlevel_discharge": lambda: features(get("/v2/waterlevel-discharge")),
            "cctv": cctv,
            "weather": lambda: features(get("/v2/weather")),
            "watergate": lambda: features(get("/v2/watergate")),
            "large_dam": lambda: features(get("/v2/large-dam/daily-geo-json")),
            "radar_sites": radar_sites,
            "radar_frames": radar_tiles,
        }
        for name, fn in jobs.items():
            try:
                rows = fn()
                with open(os.path.join(out, name + ".json"), "w") as fh:
                    json.dump(rows, fh, ensure_ascii=False)
                print(f"  {len(rows):>6}  {name}.json")
            except Exception as exc:
                print(f"  FAILED  {name}: {exc}")
            time.sleep(0.3)

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
