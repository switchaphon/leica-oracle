#!/usr/bin/env python3
"""
hii_pull.py - pull water level / rainfall telemetry from HII open data.

Source : https://tiservice.hii.or.th/opendata/data_catalog/water_level/
Catalog: https://data.hii.or.th/dataset/water-level  (CKAN, package 334aa20b)
Licence: Creative Commons Attribution Non-Commercial (CC BY-NC)
         Non-commercial only. Attribute สถาบันสารสนเทศทรัพยากรน้ำ (HII).

No API key. No auth. Plain Apache directory index + CKAN datastore API.

Data shape
  station CSV : station_code, measure_datetime, water_level, quality_flag
  cadence     : every 10 minutes (144 rows/day, 4320 rows in a 30-day month)
  unit        : m.rtk (metres above mean sea level)
  missing     : quality_flag "null", or water_level in -999 / 9999 / 999999 / "-"
  coverage    : 2012-01 through 2026-07 (verified 2026-09-03)

Verbs
  stations                      download + summarise the 1396-station metadata
  months                        list months that actually hold files for a year
  pull   --station X --from ... download per-station monthly CSVs
  year   --year 2025            download the whole-year zip (about 40-70 MB)
"""

import argparse, csv, io, os, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://tiservice.hii.or.th/opendata/data_catalog/water_level"
CKAN = "https://data.hii.or.th/api/3/action"
META_RESOURCE = "47274e2b-c905-4762-b025-11ca9067d107"
UA = "Mozilla/5.0 (compatible; leica-oracle/1.0; research use)"
MISSING = {"-999", "9999", "999999", "-", "", "-999.0", "9999.0", "999999.0"}


def plausible(f):
    """True when a parsed reading is a real level, not a missing-data marker.

    Documented markers are -999 / 9999 / 999999, but the 2012-2024 files also
    hold strays such as 999976 and 999997, so screen by range.
    """
    return -900 < f < 9000


def get(url, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def listing(url):
    """Parse an Apache mod_autoindex page into entry names."""
    import re, html
    body = get(url).decode("utf-8", "replace")
    out = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', body):
        if href.startswith("?") or href.startswith("/"):
            continue
        out.append(html.unescape(href))
    return out


def cmd_stations(args):
    """Metadata is in CKAN's datastore, so it is queryable without downloading."""
    raw = get(f"{BASE}/0all_stn_metadata.csv")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    keep = rows
    if args.type:
        keep = [r for r in keep if args.type in r["Station_Type_Name"]]
    if args.province:
        keep = [r for r in keep if args.province in r["Province_Name"]]
    if args.basin:
        keep = [r for r in keep if args.basin in (r["Basin_Name"] + r["Sub_Basin_Name"])]
    print(f"# {len(keep)} of {len(rows)} stations", file=sys.stderr)
    w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(keep)


def cmd_months(args):
    names = [n.rstrip("/") for n in listing(f"{BASE}/{args.year}/")]
    for m in sorted(n for n in names if n.isdigit()):
        n = sum(1 for f in listing(f"{BASE}/{args.year}/{m}/") if f.endswith(".csv"))
        print(f"{m}  {n:4d} files{'   (empty - not published yet)' if n == 0 else ''}")


def months_between(a, b):
    y, m = int(a[:4]), int(a[4:])
    ey, em = int(b[:4]), int(b[4:])
    while (y, m) <= (ey, em):
        yield f"{y}{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def cmd_pull(args):
    os.makedirs(args.out, exist_ok=True)
    ok = skip = fail = 0
    for st in args.station:
        for ym in months_between(args.frm, args.to):
            dest = os.path.join(args.out, f"{st}_{ym}.csv")
            if os.path.exists(dest) and os.path.getsize(dest) > 0 and not args.force:
                skip += 1
                continue
            url = f"{BASE}/{ym[:4]}/{ym}/{st}.csv"
            try:
                body = get(url)
            except urllib.error.HTTPError as e:
                print(f"  MISS {st} {ym}  http {e.code}", file=sys.stderr)
                fail += 1
                time.sleep(args.delay)
                continue
            with open(dest, "wb") as f:
                f.write(body)
            n = body.count(b"\n") - 1
            print(f"  ok   {st} {ym}  {len(body):>8,} bytes  {n:>5} rows")
            ok += 1
            time.sleep(args.delay)
    print(f"\ndownloaded={ok} skipped={skip} missing={fail} -> {args.out}", file=sys.stderr)


def cmd_year(args):
    os.makedirs(args.out, exist_ok=True)
    url = f"{BASE}/0zip_file/{args.year}.zip"
    dest = os.path.join(args.out, f"{args.year}.zip")
    print(f"GET {url}", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done/1048576:6.1f} / {total/1048576:.1f} MB", end="", file=sys.stderr)
    print(f"\nsaved {dest}", file=sys.stderr)


def cmd_peak(args):
    """Summarise already-downloaded station CSVs: peak, min, missing rate."""
    for path in args.files:
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
        vals, miss = [], 0
        for r in rows:
            v = (r.get("water_level") or "").strip()
            if v in MISSING or (r.get("quality_flag") or "").lower() == "null":
                miss += 1
                continue
            try:
                fv = float(v)
            except ValueError:
                miss += 1
                continue
            if plausible(fv):
                vals.append((fv, r["measure_datetime"]))
            else:
                miss += 1
        if not vals:
            print(f"{os.path.basename(path)}: no usable rows ({len(rows)} total)")
            continue
        hi, lo = max(vals), min(vals)
        print(f"{os.path.basename(path)}: rows={len(rows)} usable={len(vals)} "
              f"missing={miss/len(rows)*100:.1f}%  peak={hi[0]:.2f} @ {hi[1]}  min={lo[0]:.2f}")


def load_meta():
    raw = get(f"{BASE}/0all_stn_metadata.csv")
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))


def select_stations(rows, basins=None, provinces=None, regions=None, stype="ระดับน้ำ"):
    keep = [r for r in rows if not stype or stype in r["Station_Type_Name"]]
    if basins:
        keep = [r for r in keep if any(b in (r["Basin_Name"] or "") for b in basins)]
    if provinces:
        keep = [r for r in keep if any(b in (r["Province_Name"] or "") for b in provinces)]
    if regions:
        keep = [r for r in keep if any(b in (r["Region_name"] or "") for b in regions)]
    return keep


def cmd_basins(args):
    import collections
    rows = load_meta()
    wl = [r for r in rows if args.type in r["Station_Type_Name"]] if args.type else rows
    print(f"# {len(wl)} stations of type {args.type or 'ALL'}")
    for k, v in collections.Counter(r["Basin_Name"] or "(blank)" for r in wl).most_common():
        print(f"  {v:5}  {k}")


def fetch_zip(year, cache, delay=1.0):
    """Download a year archive into cache, resuming/skipping when already whole."""
    os.makedirs(cache, exist_ok=True)
    dest = os.path.join(cache, f"{year}.zip")
    url = f"{BASE}/0zip_file/{year}.zip"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            remote = int(r.headers.get("Content-Length") or 0)
    except urllib.error.HTTPError as e:
        print(f"  no archive for {year} (http {e.code})", file=sys.stderr)
        return None
    if os.path.exists(dest) and remote and os.path.getsize(dest) == remote:
        print(f"  {year}.zip cached ({remote/1048576:.1f} MB)", file=sys.stderr)
        return dest
    print(f"  {year}.zip downloading {remote/1048576:.1f} MB", file=sys.stderr, end="", flush=True)
    with urllib.request.urlopen(req, timeout=900) as r, open(dest, "wb") as f:
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
        print(f" -> {done/1048576:.1f} MB", file=sys.stderr)
    time.sleep(delay)
    return dest


HEADER = b"station_code,measure_datetime,water_level,quality_flag\n"


def normalise(blob, code):
    """HII changed the CSV schema in 2025. Return rows in the 2025 shape.

    2012-2024 : date,time,water_lv                                   (3 cols, missing = "-")
    2025-2026 : station_code,measure_datetime,water_level,quality_flag (4 cols)
    """
    lines = blob.split(b"\n")
    if not lines:
        return b""
    head = lines[0].lstrip(b"\xef\xbb\xbf").strip().lower()
    body = lines[1:] if (head.startswith(b"station_code") or head.startswith(b"date")) else lines
    if head.startswith(b"station_code"):
        out = [ln for ln in body if ln.strip()]
        return b"\n".join(out) + (b"\n" if out else b"")
    # old three-column form: date,time,water_lv -> code,"date time",level,(blank flag)
    pre = code.encode() + b","
    out = []
    for ln in body:
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split(b",")
        if len(parts) < 3:
            continue
        out.append(pre + parts[0] + b" " + parts[1] + b"," + parts[2] + b",")
    return b"\n".join(out) + (b"\n" if out else b"")


def cmd_bulk(args):
    """Year archives -> normalised, merged, one file per station.

    Streams year by year straight to disk so memory stays flat and partial
    results are visible while a long run is still going.
    """
    import zipfile, collections
    meta = load_meta()
    sel = select_stations(meta, args.basin, args.province, args.region, args.type)
    codes = {r["Station_Code"] for r in sel}
    if not codes:
        print("no stations matched", file=sys.stderr)
        return 1
    print(f"{len(codes)} stations matched", file=sys.stderr)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "_stations.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=meta[0].keys())
        w.writeheader()
        w.writerows(sorted(sel, key=lambda r: r["Station_Code"]))

    started = set()
    rows_per_station = collections.Counter()
    schema_seen = collections.Counter()

    for year in range(args.from_year, args.to_year + 1):
        zp = fetch_zip(str(year), args.cache, args.delay)
        if not zp:
            continue
        try:
            z = zipfile.ZipFile(zp)
        except zipfile.BadZipFile:
            print(f"  {year}.zip is not a valid archive, skipped", file=sys.stderr)
            continue
        wanted = []
        for name in z.namelist():
            fn = name.split("/")[-1]
            if not fn.endswith(".csv") or fn.startswith("0"):
                continue
            code = fn[:-4]
            if code in codes:
                wanted.append((name.split("/")[-2], code, name))
        wanted.sort()
        n = 0
        for ym, code, name in wanted:
            blob = z.read(name)
            head = blob.split(b"\n", 1)[0].lstrip(b"\xef\xbb\xbf").strip().lower()
            schema_seen["2025-form" if head.startswith(b"station_code") else "pre-2025-form"] += 1
            rows = normalise(blob, code)
            if not rows:
                continue
            dest = os.path.join(args.out, f"{code}.csv")
            if code not in started:
                with open(dest, "wb") as f:
                    f.write(HEADER)
                started.add(code)
            with open(dest, "ab") as f:
                f.write(rows)
            rows_per_station[code] += rows.count(b"\n")
            n += 1
        print(f"  {year}: merged {n} monthly files across {len({c for _, c, _ in wanted})} stations",
              file=sys.stderr)

    print(f"\nwrote {len(started)} station files -> {args.out}", file=sys.stderr)
    print(f"schema mix: {dict(schema_seen)}", file=sys.stderr)
    print(f"total rows: {sum(rows_per_station.values()):,}", file=sys.stderr)
    missing = sorted(codes - started)
    if missing:
        print(f"{len(missing)} matched stations had no files in {args.from_year}-{args.to_year}: "
              f"{', '.join(missing[:12])}{' ...' if len(missing) > 12 else ''}", file=sys.stderr)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stations", help="dump station metadata as CSV to stdout")
    s.add_argument("--type", help="filter Station_Type_Name, e.g. ระดับน้ำ or น้ำฝน")
    s.add_argument("--province", help="filter Province_Name, e.g. สงขลา")
    s.add_argument("--basin", help="filter Basin_Name or Sub_Basin_Name")
    s.set_defaults(func=cmd_stations)

    s = sub.add_parser("months", help="list months holding files for a year")
    s.add_argument("--year", required=True)
    s.set_defaults(func=cmd_months)

    s = sub.add_parser("pull", help="download per-station monthly CSVs")
    s.add_argument("--station", nargs="+", required=True, help="station codes, e.g. SLA001 ONE037")
    s.add_argument("--from", dest="frm", required=True, help="start YYYYMM")
    s.add_argument("--to", required=True, help="end YYYYMM")
    s.add_argument("--out", default="./hii_data")
    s.add_argument("--delay", type=float, default=0.3, help="seconds between requests")
    s.add_argument("--force", action="store_true", help="re-download existing files")
    s.set_defaults(func=cmd_pull)

    s = sub.add_parser("year", help="download a whole-year zip")
    s.add_argument("--year", required=True)
    s.add_argument("--out", default="./hii_data")
    s.set_defaults(func=cmd_year)

    s = sub.add_parser("peak", help="summarise downloaded CSVs")
    s.add_argument("files", nargs="+")
    s.set_defaults(func=cmd_peak)

    s = sub.add_parser("basins", help="list basins with station counts")
    s.add_argument("--type", default="ระดับน้ำ")
    s.set_defaults(func=cmd_basins)

    s = sub.add_parser("bulk", help="year archives -> merged per-station time-series")
    s.add_argument("--basin", nargs="*", help="basin substrings, e.g. เจ้าพระยา ท่าจีน")
    s.add_argument("--province", nargs="*")
    s.add_argument("--region", nargs="*", help="e.g. ภาคกลาง")
    s.add_argument("--type", default="ระดับน้ำ", help="station type, blank for all")
    s.add_argument("--from-year", type=int, default=2012, dest="from_year")
    s.add_argument("--to-year", type=int, default=2026, dest="to_year")
    s.add_argument("--out", default="./hii_basin")
    s.add_argument("--cache", default="./hii_zips", help="where year archives are kept")
    s.add_argument("--delay", type=float, default=1.0)
    s.set_defaults(func=cmd_bulk)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
