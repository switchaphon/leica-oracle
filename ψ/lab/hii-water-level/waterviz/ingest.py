#!/usr/bin/env python3
"""
ingest.py - pull Chao Phraya / Tha Chin / Pa Sak water level into SQLite,
then export a compact snapshot for the web page.

  python3 ingest.py --db ~/hii-data/waterviz.db --days 30
  python3 ingest.py --db ~/hii-data/waterviz.db --export snapshot.json

Source: api-v3.thaiwater.net public feed (HII / สสน.). No key, no auth.
Licence on the underlying open data is CC BY-NC.
"""

import argparse, json, os, sqlite3, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta

API = "https://api-v3.thaiwater.net/api/v1/thaiwater30"
UA = "Mozilla/5.0 (compatible; leica-waterviz/1.0)"
# The Chao Phraya forms at Pak Nam Pho where Ping, Wang, Yom and Nan meet, so
# the upstream four plus Sakae Krang are the catchment that feeds everything
# downstream. Tha Chin branches off the Chao Phraya at Chai Nat.
BASINS = ("เจ้าพระยา", "ท่าจีน", "ป่าสัก", "ปิง", "วัง", "ยม", "น่าน", "สะแกกรัง")

SCHEMA = """
CREATE TABLE IF NOT EXISTS station (
  station_id   INTEGER PRIMARY KEY,
  code         TEXT,
  name_th      TEXT,
  name_en      TEXT,
  lat          REAL,
  lon          REAL,
  basin        TEXT,
  agency       TEXT,
  agency_full  TEXT,
  province     TEXT,
  amphoe       TEXT,
  tambon       TEXT,
  river        TEXT,
  bank_level   REAL,
  ground_level REAL
);
CREATE TABLE IF NOT EXISTS reading (
  station_id INTEGER NOT NULL,
  ts         TEXT    NOT NULL,   -- 'YYYY-MM-DD HH:MM', Asia/Bangkok
  msl        REAL,
  source     TEXT,               -- 'graph' | 'live' | NULL for rows predating this column
  PRIMARY KEY (station_id, ts)
);
CREATE INDEX IF NOT EXISTS reading_station_ts ON reading(station_id, ts);
"""


def get(path, params=None, timeout=120):
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def th(d, k="th"):
    return (d or {}).get(k) if isinstance(d, dict) else None


def num(v):
    if v in (None, "", "-"):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f >= 9000 or f <= -900 else f


def migrate(con):
    """Add `source` to a database that predates it.

    Rows written before this column existed stay NULL on purpose. Both writers
    used INSERT OR REPLACE on the same (station_id, ts) key, so which of them
    last touched an old row is genuinely unrecoverable - labelling them by
    guesswork would invent provenance that was never recorded.
    """
    cols = {r[1] for r in con.execute("PRAGMA table_info(reading)")}
    if "source" not in cols:
        con.execute("ALTER TABLE reading ADD COLUMN source TEXT")
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM reading WHERE source IS NULL").fetchone()[0]
        print(f"migrated: added reading.source, {n:,} existing rows left unlabelled",
              file=sys.stderr)
    con.execute("CREATE INDEX IF NOT EXISTS reading_source ON reading(source)")
    con.commit()


def open_db(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    con = sqlite3.connect(path, timeout=60)
    # The 15-minute live poll can land while a nightly backfill is mid-flight.
    # WAL lets a reader and a writer coexist; busy_timeout makes a writer wait
    # its turn instead of raising "database is locked" and losing the poll.
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=60000")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(SCHEMA)
    migrate(con)
    return con


def sync_stations(con):
    """Refresh the station table and write the current reading for each."""
    d = get("public/waterlevel_load")["waterlevel_data"]["data"]
    rows, now = [], []
    for s in d:
        basin = th((s.get("basin") or {}).get("basin_name")) or ""
        if not any(b in basin for b in BASINS):
            continue
        st = s.get("station") or {}
        geo = s.get("geocode") or {}
        ag = s.get("agency") or {}
        msl = num(s.get("waterlevel_msl"))
        diff = num(s.get("diff_wl_bank"))
        # For 60 of the 154 stations the feed echoes the level back as
        # diff_wl_bank (identical to the millimetre). That is a placeholder for
        # "no bank reference", not a real distance - deriving a bank from it
        # yields exactly twice the water level. Drop it; waterlevel_graph's
        # min_bank fills these in later where the station publishes one.
        if msl is not None and diff is not None and abs(msl - diff) < 1e-9:
            diff = None
        rows.append((
            st.get("id"), st.get("tele_station_oldcode"),
            th(st.get("tele_station_name")), th(st.get("tele_station_name"), "en"),
            num(st.get("tele_station_lat")), num(st.get("tele_station_long")),
            basin, th(ag.get("agency_shortname")), th(ag.get("agency_name")),
            th(geo.get("province_name")) or th(geo.get("area_name")),
            th(geo.get("amphoe_name")), th(geo.get("tumbon_name")),
            s.get("river_name"),
            round(msl + diff, 3) if (msl is not None and diff is not None) else None,
            None,
        ))
        ts = s.get("waterlevel_datetime")
        if ts and msl is not None:
            now.append((st.get("id"), ts[:16], msl, "live"))
    con.executemany("""INSERT INTO station VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(station_id) DO UPDATE SET
                         code=excluded.code, name_th=excluded.name_th, lat=excluded.lat,
                         lon=excluded.lon, basin=excluded.basin, agency=excluded.agency,
                         agency_full=excluded.agency_full, province=excluded.province,
                         amphoe=excluded.amphoe, tambon=excluded.tambon,
                         river=excluded.river,
                         bank_level=COALESCE(excluded.bank_level, station.bank_level)""", rows)
    con.executemany("INSERT OR REPLACE INTO reading (station_id,ts,msl,source) "
                    "VALUES (?,?,?,?)", now)
    con.commit()
    return len(rows)


def backfill(con, days, delay):
    """One waterlevel_graph call per station. The endpoint caps at 52,704 points."""
    end = datetime.now()
    start = end - timedelta(days=days)
    ids = [r[0] for r in con.execute("SELECT station_id FROM station ORDER BY station_id")]
    ok = fail = 0
    for i, sid in enumerate(ids, 1):
        try:
            d = get("public/waterlevel_graph", {
                "station_type": "tele_waterlevel", "station_id": sid,
                "start_date": start.strftime("%Y-%m-%d %H:%M"),
                "end_date": end.strftime("%Y-%m-%d %H:%M"),
            })["data"]
        except Exception as e:
            print(f"  [{i}/{len(ids)}] {sid} FAILED {e}", file=sys.stderr)
            fail += 1
            continue
        pts = [(sid, p["datetime"][:16], num(p.get("value")), "graph")
               for p in (d.get("graph_data") or []) if p.get("datetime")]
        pts = [p for p in pts if p[2] is not None]
        if pts:
            con.executemany("INSERT OR REPLACE INTO reading (station_id,ts,msl,source) "
                            "VALUES (?,?,?,?)", pts)
        bank, ground = num(d.get("min_bank")), num(d.get("ground_level"))
        con.execute("UPDATE station SET bank_level=COALESCE(?,bank_level), "
                    "ground_level=COALESCE(?,ground_level) WHERE station_id=?",
                    (bank, ground, sid))
        con.commit()
        ok += 1
        print(f"  [{i}/{len(ids)}] {sid} {len(pts):>5} pts", file=sys.stderr)
        time.sleep(delay)
    return ok, fail


def export(con, path, days, target_points):
    """Write a payload the page can hold in memory.

    Two series per station, because one cannot serve both zoom levels:
      t/v      the whole window, downsampled, for the 7 and 30 day views
      t24/v24  the last 24 hours untouched, so the default view keeps its
               10-minute cadence instead of showing seven lonely points

    Timestamps ship as integer minutes from a single base rather than as
    "YYYY-MM-DD HH:MM" strings - same information, roughly a third of the bytes,
    which matters at 518 stations.
    """
    now = datetime.now()
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    cut24 = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
    base = datetime.strptime(cutoff, "%Y-%m-%d %H:%M").replace(minute=0)
    mins = lambda t: int((datetime.strptime(t, "%Y-%m-%d %H:%M") - base).total_seconds() // 60)

    def thin(pts, target):
        """Keep the extreme of each bucket so peaks survive the reduction."""
        if len(pts) <= target:
            return pts
        step = len(pts) / target
        keep, i = [], 0.0
        while int(i) < len(pts):
            bucket = pts[int(i):int(i + step) or int(i) + 1]
            if bucket:
                keep.append(max(bucket, key=lambda p: p[1]) if len(bucket) > 1 else bucket[0])
            i += step
        return keep

    stations = []
    for r in con.execute("""SELECT station_id, code, name_th, lat, lon, basin, agency,
                                   agency_full, province, amphoe, tambon, river,
                                   bank_level, ground_level
                            FROM station WHERE lat IS NOT NULL ORDER BY name_th"""):
        sid = r[0]
        pts = list(con.execute(
            "SELECT ts, msl FROM reading WHERE station_id=? AND ts>=? ORDER BY ts", (sid, cutoff)))
        fine = [p for p in pts if p[0] >= cut24]
        coarse = thin(pts, target_points)
        last = pts[-1] if pts else (None, None)
        stations.append({
            "id": sid, "code": r[1], "name": r[2], "lat": r[3], "lon": r[4],
            "basin": r[5], "agency": r[6], "agencyFull": r[7],
            "province": r[8], "amphoe": r[9], "tambon": r[10], "river": r[11],
            "bank": r[12], "ground": r[13],
            "last": last[1], "lastAt": last[0],
            "t": [mins(p[0]) for p in coarse], "v": [p[1] for p in coarse],
            "t24": [mins(p[0]) for p in fine], "v24": [p[1] for p in fine],
        })
    out = {
        "generatedAt": now.strftime("%Y-%m-%d %H:%M"),
        "base": base.strftime("%Y-%m-%d %H:%M"),
        "days": days,
        "dbRows": con.execute("SELECT COUNT(*) FROM reading").fetchone()[0],
        "dbFrom": con.execute("SELECT MIN(ts) FROM reading").fetchone()[0],
        "bySource": dict(con.execute(
            "SELECT COALESCE(source,'ไม่ระบุ'), COUNT(*) FROM reading GROUP BY 1")),
        "source": "api-v3.thaiwater.net (HII / สสน.)",
        "licence": "CC BY-NC",
        "stations": stations,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    return len(stations), os.path.getsize(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.path.expanduser("~/hii-data/waterviz.db"))
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--delay", type=float, default=0.4)
    p.add_argument("--skip-backfill", action="store_true")
    p.add_argument("--export")
    p.add_argument("--export-days", type=int, default=30)
    p.add_argument("--points", type=int, default=220, help="points per station in the export")
    a = p.parse_args()

    con = open_db(a.db)
    n = sync_stations(con)
    print(f"stations across {len(BASINS)} basins: {n}", file=sys.stderr)
    if not a.skip_backfill:
        ok, fail = backfill(con, a.days, a.delay)
        print(f"backfill: ok={ok} failed={fail}", file=sys.stderr)
    tot = con.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
    print(f"readings in db: {tot:,}", file=sys.stderr)
    if a.export:
        ns, sz = export(con, a.export, a.export_days, a.points)
        print(f"exported {ns} stations -> {a.export} ({sz/1024:.0f} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
