#!/usr/bin/env python3
"""
hii_live.py - HII / ThaiWater ingest for RPRO. Emits InfluxDB line protocol.

Two sources, one output format:

  live       api-v3.thaiwater.net public feed. Every station, current reading.
             waterlevel_load  1,407 water-level stations
             rain_24h         4,433 rain gauges
             rain_today       4,499
             rain_yesterday   3,609
             Poll every 10-15 min. Telemetry lags wall clock by about 10-15 min.

  backfill   waterlevel_graph, one station at a time, 10-minute resolution.
             HARD CAP 52,704 points per request (about one year). Asking for
             14 years returns the same 52,704 points, silently. Always window
             by year and stitch, never trust a single wide request.

Timestamps from the API carry no timezone and are Asia/Bangkok. Converted to
UTC nanoseconds here, which is what Influx wants.

Usage
  python3 hii_live.py live --measurement water_level        > wl.lp
  python3 hii_live.py live --source rain_24h                > rain.lp
  python3 hii_live.py backfill --station-id 568 --year 2025 > cpy001_2025.lp
  python3 hii_live.py stations                              # id/code/basin join table

  # straight into Influx 2.x
  python3 hii_live.py live | curl -s --data-binary @- \\
    -H "Authorization: Token $INFLUX_TOKEN" \\
    "http://influx:8086/api/v2/write?org=rpro&bucket=hii&precision=ns"
"""

import argparse, json, signal, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api-v3.thaiwater.net/api/v1/thaiwater30"
UA = "Mozilla/5.0 (compatible; rpro-ingest/1.0)"
BKK = timezone(timedelta(hours=7))

LIVE_SOURCES = {
    "waterlevel_load": ("waterlevel_data", "data"),
    "rain_24h": (None, "data"),
    "rain_today": (None, "data"),
    "rain_yesterday": (None, "data"),
}


def fetch(path, params=None, timeout=180):
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def esc_tag(v):
    """Influx tag keys/values escape comma, space, equals."""
    return str(v).replace("\\", "\\\\").replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")


def to_ns(s):
    """'2026-09-03 13:50' in Asia/Bangkok -> UTC nanoseconds."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return int(datetime.strptime(s, fmt).replace(tzinfo=BKK).timestamp() * 1_000_000_000)
        except ValueError:
            continue
    return None


def num(v):
    if v in (None, "", "-"):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    # HII missing-data markers. The documented codes are -999 / 9999 / 999999,
    # but the 2012-2024 corpus also contains stray values like 999976 and
    # 999997, so screen by range rather than by an exact list. The highest
    # genuine reading observed nationally is about 454 m MSL.
    return None if f >= 9000 or f <= -900 else f


def line(meas, tags, fields, ns):
    """One Influx line. Returns None when there is nothing worth writing."""
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields or ns is None:
        return None
    tagpart = "".join(f",{esc_tag(k)}={esc_tag(v)}" for k, v in tags.items() if v not in (None, ""))
    fieldpart = ",".join(f"{k}={v}" for k, v in fields.items())
    return f"{meas}{tagpart} {fieldpart} {ns}"


def th(d, key="th"):
    return d.get(key) if isinstance(d, dict) else d


def cmd_live(args):
    root, leaf = LIVE_SOURCES[args.source]
    d = fetch(f"public/{args.source}")
    recs = (d[root] if root else d)[leaf]
    n = 0
    for s in recs:
        st = s.get("station") or {}
        geo = s.get("geocode") or {}
        tags = {
            "station_code": st.get("tele_station_oldcode") or st.get("station_code"),
            "station_id": st.get("id"),
            "station_type": s.get("station_type") or st.get("tele_station_type"),
            "basin": th((s.get("basin") or {}).get("basin_name")),
            "agency": th((s.get("agency") or {}).get("agency_shortname")),
            "province": th(geo.get("province_name")) or th(geo.get("area_name")),
            "amphoe": th(geo.get("amphoe_name")),
            "river": s.get("river_name"),
        }
        if not tags["station_code"] and not tags["station_id"]:
            continue
        fields = {
            "msl": num(s.get("waterlevel_msl")),
            "msl_prev": num(s.get("waterlevel_msl_previous")),
            "level_m": num(s.get("waterlevel_m")),
            "flow_rate": num(s.get("flow_rate")),
            "discharge": num(s.get("discharge")),
            "storage_percent": num(s.get("storage_percent")),
            "diff_wl_bank": num(s.get("diff_wl_bank")),
            "situation_level": num(s.get("situation_level")),
            # rain feeds
            "rain_24h": num(s.get("rain_24h")),
            "rain_today": num(s.get("rain_today")),
            "rainfall": num(s.get("rainfall")),
        }
        ts = s.get("waterlevel_datetime") or s.get("rainfall_datetime") or s.get("log_datetime")
        ln = line(args.measurement, tags, fields, to_ns(ts) if ts else None)
        if ln:
            print(ln)
            n += 1
    print(f"# {n} points from {args.source}", file=sys.stderr)


def cmd_backfill(args):
    """One year per request. The API caps at 52,704 points and does not say so."""
    y = args.year
    d = fetch("public/waterlevel_graph", {
        "station_type": "tele_waterlevel",
        "station_id": args.station_id,
        "start_date": f"{y}-01-01 00:00",
        "end_date": f"{y + 1}-01-01 00:00",
    })
    body = d.get("data", d)
    pts = body.get("graph_data", [])
    if len(pts) >= 52704:
        print(f"# WARNING station {args.station_id} year {y} hit the 52,704-point cap; "
              f"narrow the window or expect truncation", file=sys.stderr)
    tags = {"station_id": args.station_id, "station_code": args.station_code or "", "source": "graph"}
    n = 0
    for p in pts:
        ln = line(args.measurement, tags,
                  {"msl": num(p.get("value")),
                   "value_out": num(p.get("value_out")),
                   "discharge": num(p.get("discharge"))},
                  to_ns(p.get("datetime")))
        if ln:
            print(ln)
            n += 1
    for k in ("min_bank", "warning_level", "critical_level", "ground_level", "qmax"):
        if body.get(k) is not None:
            print(f"# {k}={body[k]}", file=sys.stderr)
    print(f"# {n} points, station {args.station_id}, year {y}", file=sys.stderr)


def cmd_stations(args):
    """The join table between the live API and the open-data file names."""
    import csv
    d = fetch("public/waterlevel_load")
    w = csv.writer(sys.stdout)
    w.writerow(["station_id", "station_code", "name_th", "name_en", "lat", "lon",
                "basin", "province", "amphoe", "agency", "river"])
    for s in d["waterlevel_data"]["data"]:
        st = s.get("station") or {}
        geo = s.get("geocode") or {}
        w.writerow([st.get("id"), st.get("tele_station_oldcode") or "",
                    th(st.get("tele_station_name")), th(st.get("tele_station_name"), "en"),
                    st.get("tele_station_lat"), st.get("tele_station_long"),
                    th((s.get("basin") or {}).get("basin_name")),
                    th(geo.get("province_name")) or th(geo.get("area_name")),
                    th(geo.get("amphoe_name")),
                    th((s.get("agency") or {}).get("agency_shortname")),
                    s.get("river_name") or ""])


def cmd_bounds(args):
    """Per-station QC bounds, derived from one live snapshot.

    bank_level = waterlevel_msl + diff_wl_bank. Checked against the
    waterlevel_graph min_bank for CPY001: 26.05 derived vs 26.06 reported.

    Use these to gate ingest. The 2012-2024 corpus carries a small number of
    physically impossible readings that are not sentinels - CPY001 holds a
    -20.10 and a 34.86 among 545,346 otherwise clean values (0.011%). They
    survive a sentinel filter and will wreck any min/max you compute.
    """
    import csv as _csv
    d = fetch("public/waterlevel_load")
    w = _csv.writer(sys.stdout)
    w.writerow(["station_code", "station_id", "name_th", "msl_now", "diff_wl_bank",
                "bank_level", "accept_min", "accept_max"])
    n = 0
    for s_ in d["waterlevel_data"]["data"]:
        st = s_.get("station") or {}
        code = st.get("tele_station_oldcode")
        msl = num(s_.get("waterlevel_msl"))
        diff = num(s_.get("diff_wl_bank"))
        if msl is None:
            continue
        bank = round(msl + diff, 3) if diff is not None else None
        # generous envelope: never below bank minus 30 m, never above bank plus 10 m
        lo = round(bank - 30, 3) if bank is not None else None
        hi = round(bank + 10, 3) if bank is not None else None
        w.writerow([code or "", st.get("id"), th(st.get("tele_station_name")),
                    msl, diff if diff is not None else "",
                    bank if bank is not None else "",
                    lo if lo is not None else "", hi if hi is not None else ""])
        n += 1
    print(f"# {n} stations", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("live", help="current readings, all stations, as line protocol")
    s.add_argument("--source", default="waterlevel_load", choices=sorted(LIVE_SOURCES))
    s.add_argument("--measurement", default="water_level")
    s.set_defaults(func=cmd_live)

    s = sub.add_parser("backfill", help="one station, one year, 10-minute resolution")
    s.add_argument("--station-id", required=True)
    s.add_argument("--station-code", default="")
    s.add_argument("--year", type=int, required=True)
    s.add_argument("--measurement", default="water_level")
    s.set_defaults(func=cmd_backfill)

    s = sub.add_parser("stations", help="station_id / station_code join table as CSV")
    s.set_defaults(func=cmd_stations)

    s = sub.add_parser("bounds", help="per-station QC accept range, derived from a live snapshot")
    s.set_defaults(func=cmd_bounds)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    # let `| head` close the pipe without a traceback
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    main()
